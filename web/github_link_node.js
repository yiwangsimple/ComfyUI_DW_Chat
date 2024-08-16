//@ts-nocheck
import { app } from "../../scripts/app.js";

const iconSvg = `<svg class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="5348" width="200" height="200"><path d="M146.863158 0h538.947368l296.421053 296.421053v619.789473c0 59.284211-48.505263 107.789474-107.789474 107.789474H146.863158c-59.284211 0-107.789474-48.505263-107.789474-107.789474V107.789474c0-59.284211 48.505263-107.789474 107.789474-107.789474z" fill="#2F77F1" p-id="5349"></path><path d="M688.505263 0l296.421053 296.421053h-296.421053V0zM549.726316 661.557895H142.821053c-14.821053 0-25.6-12.126316-25.6-25.6V633.263158c0-14.821053 12.126316-25.6 25.6-25.6h406.905263c13.473684 0 25.6 12.126316 25.6 25.6v2.694737c0 13.473684-10.778947 25.6-25.6 25.6z m-134.736842-350.31579H142.821053c-14.821053 0-25.6-10.778947-25.6-25.6V282.947368c0-14.821053 12.126316-25.6 25.6-25.6h272.168421c13.473684 0 25.6 12.126316 25.6 25.6v2.694737c0 13.473684-10.778947 25.6-25.6 25.6z m-272.168421 121.263158h245.221052c13.473684 0 25.6 12.126316 25.6 25.6v2.694737c0 13.473684-12.126316 25.6-25.6 25.6H142.821053c-14.821053 0-25.6-10.778947-25.6-25.6V458.105263c0-14.821053 12.126316-25.6 25.6-25.6z" fill="#AFFCFE"></path></svg>`

const cacheNodePositonMap = new Map();

function formatExecutionTime(time) {
    return `${(time / 1000.0).toFixed(2)}s`;
}

const drawPaperPlaneIcon = function(node, orig, restArgs) {
  let ctx = restArgs[0];
  const r = orig?.apply?.(node, restArgs);

  if (!node.flags.collapsed && node.constructor.title_mode != LiteGraph.NO_TITLE) {
    // Check if the paper plane icon should be displayed
    if (app.ui.settings.getSettingValue("DW.NodeGithubLink.ShowIcon", true)) {
      // Draw paper plane icon
      const paperPlaneIcon = '⭐️';
      let fgColor = "white";

      ctx.save();
      ctx.font = "16px sans-serif";
      const sz = ctx.measureText(paperPlaneIcon);
      ctx.beginPath();
      ctx.fillStyle = fgColor;
      const x = 4; // Left position
      const y = -34; // Top position
      ctx.fillText(paperPlaneIcon, x, y);
      ctx.restore();

      const boundary = node.getBounding();
      const [ x1, y1, width, height ] = boundary
      cacheNodePositonMap.set(node.id, {
        x: [x1 + x, x1 + x + sz.width],
        y: [y1 , y1 + 18]
      })
    }

    if (node.has_errors) {
      ctx.save();
      ctx.font = "bold 14px sans-serif";
      const sz2 = ctx.measureText(node.type);
      ctx.fillStyle = 'white';
      ctx.fillText(node.type, node.size[0] / 2 - sz2.width / 2, node.size[1] / 2);
      ctx.restore();
    }

    // Draw execution time
    if (app.ui.settings.getSettingValue("DW.ExecutionTime.Enabled", true)) {
      let text = "";
      let bgColor = "#ffa500"; // Orange for ongoing execution

      if (node.ty_et_start_time !== undefined) {
          const currentTime = performance.now();
          const elapsedTime = currentTime - node.ty_et_start_time;
          text = formatExecutionTime(elapsedTime);
      } else if (node.ty_et_execution_time !== undefined) {
          text = formatExecutionTime(node.ty_et_execution_time);
          bgColor = "#29b560"; // Green for completed execution
      }

      if (text) {
          ctx.save();
          ctx.font = "12px sans-serif";
          const textSize = ctx.measureText(text);
          ctx.fillStyle = bgColor;
          ctx.beginPath();
          const paddingHorizontal = 6;
          ctx.roundRect(0, -LiteGraph.NODE_TITLE_HEIGHT - 20, textSize.width + paddingHorizontal * 2, 20, 5);
          ctx.fill();

          ctx.fillStyle = "white";
          ctx.fillText(text, paddingHorizontal, -LiteGraph.NODE_TITLE_HEIGHT - paddingHorizontal);
          ctx.restore();
      }
    }
  }
  return r
}

const getNodeGithubLink = (node) => {
  const nodeKey = node.comfyClass || node.type;
  console.log(`Trying to find GitHub link for node: ${nodeKey}`);
  
  if (window.nodeGithubMap && window.nodeGithubMap[nodeKey]) {
    console.log(`Found link for ${nodeKey}: ${window.nodeGithubMap[nodeKey]}`);
    return window.nodeGithubMap[nodeKey];
  }
  
  console.log(`No specific link found for ${nodeKey}, using default`);
  return 'https://github.com/comfyanonymous/ComfyUI';
}

const openNodeGithubLink = (node) => {
  const githubUrl = getNodeGithubLink(node);
  console.log(`Opening GitHub URL for node ${node.title} (${node.comfyClass || node.type}): ${githubUrl}`);
  window.open(githubUrl, '_blank');
}

const processMouseDown = LGraphCanvas.prototype.processMouseDown
LGraphCanvas.prototype.processMouseDown = function(e) {
  processMouseDown.apply(this, arguments)
  const { canvasX, canvasY } = e
  const nodes = app.graph._nodes
  let isClickPaperPlane = false
  for(let i = 0; i < nodes.length; i++) {
    const node = nodes[i]
    const [nL, nT, nW, nH] = node.getBounding()
    const iconX = nL + 4
    const iconY = nT - 24
    const iconX1 = nL + 24
    const iconY1 = nT - 12

    if(canvasX >= iconX && canvasX <= iconX1 && canvasY >= iconY && canvasY <= iconY1) {
      isClickPaperPlane = true
      openNodeGithubLink(node);
      e.stopPropagation();
      break
    }
  }

  if(!isClickPaperPlane) {
    // hideActiveDocs()  // Assuming this function is not needed
  }
}

// 注册前端插件
app.registerExtension({
  name: 'DW.NodeGithubLink',
  async setup() {
    try {
      const response = await fetch('/github_btn/get_github_links');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      window.nodeGithubMap = data;
      console.log('Loaded GitHub links:', window.nodeGithubMap);
      
      // 打印所有加载的链接
      Object.entries(window.nodeGithubMap).forEach(([nodeKey, url]) => {
        console.log(`Node Key: ${nodeKey}`);
        console.log(`URL: ${url}`);
        console.log('---');
      });

      // Add setting for showing/hiding the paper plane icon
      app.ui.settings.addSetting({
        id: "DW.NodeGithubLink.ShowIcon",
        name: "Show GitHub Link Icon",
        type: "boolean",
        defaultValue: true,
        onChange: (value) => {
          // Trigger a redraw of all nodes when the setting changes
          app.graph.setDirtyCanvas(true, true);
        }
      });
    } catch (error) {
      console.error('Error loading GitHub links:', error);
    }
  },
  nodeCreated: function(node, app) {
    if(!node.github_link_enabled) {
      let orig = node.onDrawForeground;
      if(!orig)
        orig = node.__proto__.onDrawForeground;
      node.onDrawForeground = function (ctx) {
        drawPaperPlaneIcon(node, orig, arguments)
      };
      node.github_link_enabled = true;

      const oDb = node.onMouseDown
      node.onMouseDown = function(e) {
        oDb?.apply(node, arguments)
        const { canvasX, canvasY } = e

        const [nLeft, nTop, nWidth, nHeight] = node.getBounding()
        const iconX = nLeft + 4
        const iconY = nTop - 30
        const iconX1 = nLeft + 24
        const iconY1 = nTop - 12
        if(canvasX >= iconX && canvasX <= iconX1 && canvasY >= iconY && canvasY <= iconY1) {
          if (app.ui.settings.getSettingValue("DW.NodeGithubLink.ShowIcon", true)) {
            openNodeGithubLink(node);
            e.preventDefault()
            e.stopPropagation()
            return false
          }
        }
      }
    }
  },
  loadedGraphNode(node, app) {
    if(!node.github_link_enabled) {
      const orig = node.onDrawForeground;
      node.onDrawForeground = function (ctx) { drawPaperPlaneIcon(node, orig, arguments) };
    }
  },
});