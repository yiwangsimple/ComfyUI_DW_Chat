import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function formatExecutionTime(time) {
    return `${(time / 1000.0).toFixed(2)}s`;
}

function getNodeName(node) {
    return node.displayName || node.name || node.title || node.type || node.constructor.name || "Unknown";
}

function drawBadge(node, orig, restArgs, totalTime, isLastNode) {
    let ctx = restArgs[0];
    const r = orig?.apply?.(node, restArgs);

    if (!node.flags.collapsed && node.constructor.title_mode != LiteGraph.NO_TITLE) {
        let text = "";
        let bgColor = "#ffa500"; // 正在执行时为橙色

        if (isLastNode && totalTime !== undefined) {
            text = `Total: ${formatExecutionTime(totalTime)}`;
            bgColor = "#EF596E"; // 高亮的红色
        } else if (node.ty_et_execution_time !== undefined) {
            text = formatExecutionTime(node.ty_et_execution_time); // 直接显示时间值
            bgColor = "#29b560"; // 执行完成后为绿色
        }

        if (!text) {
            return r;
        }

        ctx.save();
        ctx.font = "12px sans-serif";
        const textSize = ctx.measureText(text);
        const paddingHorizontal = 6;
        const badgeWidth = textSize.width + paddingHorizontal * 2;
        const badgeHeight = 20;

        ctx.clearRect(0, -LiteGraph.NODE_TITLE_HEIGHT - badgeHeight, badgeWidth, badgeHeight); // 清除当前节点的绘制内容
        ctx.fillStyle = bgColor;
        ctx.beginPath();
        ctx.roundRect(0, -LiteGraph.NODE_TITLE_HEIGHT - badgeHeight, badgeWidth, badgeHeight, 5);
        ctx.fill();

        ctx.fillStyle = "white";
        ctx.fillText(text, paddingHorizontal, -LiteGraph.NODE_TITLE_HEIGHT - paddingHorizontal);
        ctx.restore();
    }
    return r;
}

let updateInterval;
let totalExecutionStartTime;
let totalExecutionEndTime;
let lastExecutedNode;
let isExecuting = false;

function resetExecutionTimes() {
    totalExecutionStartTime = null;
    totalExecutionEndTime = null;
    lastExecutedNode = null;
    // 重置所有节点的执行时间
    app.graph._nodes.forEach(node => {
        node.ty_et_execution_time = undefined;
        node.ty_et_start_time = undefined;
    });
}

function startUpdateInterval() {
    if (!updateInterval) {
        updateInterval = setInterval(() => {
            app.graph.setDirtyCanvas(true, false);
        }, 100); // 每100毫秒更新一次
    }
}

function stopUpdateInterval() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

app.registerExtension({
    name: "DW-Utils.ExecutionTime",
    async setup() {
        app.ui.settings.addSetting({
            id: "DW.ExecutionTime.Enabled",
            name: "Show Execution Time",
            type: "boolean",
            defaultValue: true,
        });

        api.addEventListener("executing", ({ detail }) => {
            const nodeId = detail;
            if (!nodeId) {
                if (isExecuting) {
                    // 只有当之前正在执行时，才重置执行时间
                    resetExecutionTimes();
                }
                isExecuting = true;
                stopUpdateInterval();
                return;
            }

            if (!totalExecutionStartTime) {
                totalExecutionStartTime = performance.now();
            }

            const node = app.graph.getNodeById(nodeId);
            if (node) {
                node.ty_et_start_time = performance.now();
                startUpdateInterval();
            }
        });

        api.addEventListener("executed", () => {
            stopUpdateInterval();
            totalExecutionEndTime = performance.now();
            isExecuting = false;

            // 在执行完成后打印所有节点的执行时间
            app.graph._nodes.forEach(node => {
                if (node.ty_et_execution_time !== undefined) {
                    console.log(`#${node.id} [${getNodeName(node)}]: ${formatExecutionTime(node.ty_et_execution_time)}`);
                }
            });

            if (totalExecutionStartTime && totalExecutionEndTime) {
                const totalTime = totalExecutionEndTime - totalExecutionStartTime;
                console.log(`Prompt executed in ${formatExecutionTime(totalTime)}`);
            }
        });

        api.addEventListener("DW-Utils.ExecutionTime.executed", ({ detail }) => {
            const node = app.graph.getNodeById(detail.node);
            if (node) {
                node.ty_et_execution_time = detail.execution_time;
                node.ty_et_start_time = undefined;
                lastExecutedNode = node;
                app.graph.setDirtyCanvas(true, false);
            }
        });
    },
    async nodeCreated(node) {
        if (!node.ty_et_swizzled) {
            let orig = node.onDrawForeground;
            if (!orig) {
                orig = node.__proto__.onDrawForeground;
            }

            node.onDrawForeground = function (ctx) {
                let totalTime;
                if (totalExecutionStartTime && totalExecutionEndTime) {
                    totalTime = totalExecutionEndTime - totalExecutionStartTime;
                }
                if (app.ui.settings.getSettingValue("DW.ExecutionTime.Enabled", true)) {
                    drawBadge(node, orig, arguments, totalTime, node === lastExecutedNode);
                } else {
                    orig?.apply?.(node, arguments);
                }
            };
            node.ty_et_swizzled = true;
        }
    },
    async loadedGraphNode(node) {
        if (!node.ty_et_swizzled) {
            const orig = node.onDrawForeground;
            node.onDrawForeground = function (ctx) {
                let totalTime;
                if (totalExecutionStartTime && totalExecutionEndTime) {
                    totalTime = totalExecutionEndTime - totalExecutionStartTime;
                }
                if (app.ui.settings.getSettingValue("DW.ExecutionTime.Enabled", true)) {
                    drawBadge(node, orig, arguments, totalTime, node === lastExecutedNode);
                } else {
                    orig?.apply?.(node, arguments);
                }
            };
            node.ty_et_swizzled = true;
        }
    }
});