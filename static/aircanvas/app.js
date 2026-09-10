const video = document.querySelector('#video');
const stage = document.querySelector('#stage');
const drawCanvas = document.querySelector('#draw-canvas');
const guideCanvas = document.querySelector('#guide-canvas');
const drawContext = drawCanvas.getContext('2d');
const guideContext = guideCanvas.getContext('2d');
const status = document.querySelector('#status');
const cameraMessage = document.querySelector('#camera-message');
const modeLabel = document.querySelector('#mode-label');
const toolbar = document.querySelector('#toolbar');

let activeColor = '#37b7a4';
let brushSize = 6;
let erasing = false;
let previousPoint = null;
let smoothingPoints = [];
let camera;

function setStatus(text, state = 'idle') {
  status.textContent = text;
  status.dataset.state = state;
}

function sizeCanvases() {
  const width = video.videoWidth || 1280;
  const height = video.videoHeight || 720;
  [drawCanvas, guideCanvas].forEach((canvas) => {
    if (canvas.width !== width || canvas.height !== height) {
      const image = canvas === drawCanvas ? canvas.toDataURL() : null;
      canvas.width = width;
      canvas.height = height;
      if (image) {
        const restored = new Image();
        restored.onload = () => drawContext.drawImage(restored, 0, 0, width, height);
        restored.src = image;
      }
    }
  });
}

function clearCanvas() {
  drawContext.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
  previousPoint = null;
  smoothingPoints = [];
  modeLabel.textContent = 'Canvas cleared. Index finger up draws.';
}

function saveCanvas() {
  const image = drawCanvas.toDataURL('image/png');
  const link = document.createElement('a');
  link.download = 'drawing.png';
  link.href = image;
  link.click();

  const body = new URLSearchParams({ image });
  fetch('/api/save/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }, body })
    .then((response) => response.ok ? response.json() : Promise.reject())
    .then((data) => setStatus(`Saved ${data.filename}`, 'ready'))
    .catch(() => setStatus('Downloaded locally', 'ready'));
}

function getCookie(name) {
  return document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1] || '';
}

function smoothPoint(x, y) {
  smoothingPoints.push({ x, y });
  if (smoothingPoints.length > 5) smoothingPoints.shift();
  return smoothingPoints.reduce((point, current) => ({ x: point.x + current.x / smoothingPoints.length, y: point.y + current.y / smoothingPoints.length }), { x: 0, y: 0 });
}

function drawLandmarkGuide(landmarks) {
  guideContext.clearRect(0, 0, guideCanvas.width, guideCanvas.height);
  if (!landmarks) return;

  drawConnectors(guideContext, landmarks, HAND_CONNECTIONS, {
    color: '#f2f0e6',
    lineWidth: 3,
  });
  drawLandmarks(guideContext, landmarks, {
    color: '#37b7a4',
    fillColor: '#182523',
    lineWidth: 1,
    radius: 4,
  });

  const tip = landmarks[8];
  guideContext.beginPath();
  guideContext.arc(tip.x * guideCanvas.width, tip.y * guideCanvas.height, 11, 0, Math.PI * 2);
  guideContext.strokeStyle = '#f2f0e6';
  guideContext.lineWidth = 3;
  guideContext.stroke();
}

function selectToolbar(visualX, visualY) {
  if (visualY > 80 || visualX < 0 || visualX > drawCanvas.width) return;
  const toolIndex = Math.min(toolbar.children.length - 1, Math.floor(visualX / drawCanvas.width * toolbar.children.length));
  const tool = toolbar.children[toolIndex];
  if (tool.dataset.tool === 'clear') {
    clearCanvas();
  } else if (tool.dataset.tool === 'eraser') {
    erasing = true;
    brushSize = 40;
  } else if (tool.dataset.tool === 'color') {
    activeColor = tool.dataset.color;
    erasing = false;
    brushSize = 6;
  }
  toolbar.querySelector('.tool.active')?.classList.remove('active');
  tool.classList.add('active');
}

function fingersUp(landmarks) {
  const thumb = landmarks[4].x < landmarks[3].x;
  return [thumb, 8, 12, 16, 20].map((tip, index) => index === 0 ? thumb : landmarks[tip].y < landmarks[tip - 2].y);
}

function handleResults(results) {
  sizeCanvases();
  const landmarks = results.multiHandLandmarks?.[0];
  drawLandmarkGuide(landmarks);
  if (!landmarks) {
    previousPoint = null;
    smoothingPoints = [];
    modeLabel.textContent = 'Show your hand to the camera. Index finger up draws.';
    return;
  }

  const [, index, middle, ring, pinky] = fingersUp(landmarks);
  const tip = landmarks[8];
  const x = tip.x * drawCanvas.width;
  const y = tip.y * drawCanvas.height;

  if (index && middle && !ring && !pinky) {
    previousPoint = null;
    smoothingPoints = [];
    selectToolbar((1 - tip.x) * drawCanvas.width, tip.y * drawCanvas.height);
    modeLabel.textContent = 'MOVE MODE · lower your index finger to draw';
    return;
  }
  if (index && !middle && !ring && !pinky) {
    const point = smoothPoint(x, y);
    modeLabel.textContent = erasing ? 'ERASER MODE · drawing with your index finger' : 'DRAWING · move your index finger';
    drawContext.beginPath();
    if (previousPoint) drawContext.moveTo(previousPoint.x, previousPoint.y);
    else drawContext.moveTo(point.x, point.y);
    drawContext.lineTo(point.x, point.y);
    drawContext.lineCap = 'round';
    drawContext.lineJoin = 'round';
    drawContext.lineWidth = erasing ? 40 : brushSize;
    drawContext.strokeStyle = erasing ? '#263532' : activeColor;
    drawContext.stroke();
    previousPoint = point;
    return;
  }
  previousPoint = null;
  smoothingPoints = [];
  modeLabel.textContent = 'HAND DETECTED · use one finger to draw or two to move';
}

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: false });
    video.srcObject = stream;
    await video.play();
    cameraMessage.classList.add('hidden');
    setStatus('Camera ready', 'ready');
    camera = new Camera(video, { onFrame: async () => hands.send({ image: video }), width: 1280, height: 720 });
    camera.start();
  } catch (error) {
    setStatus('Camera unavailable', 'error');
    modeLabel.textContent = 'Allow camera access in your browser, then try again.';
  }
}

const hands = new Hands({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}` });
hands.setOptions({ maxNumHands: 1, modelComplexity: 1, minDetectionConfidence: 0.7, minTrackingConfidence: 0.6 });
hands.onResults(handleResults);

document.querySelector('#start-camera').addEventListener('click', startCamera);
document.addEventListener('keydown', (event) => {
  if (event.key.toLowerCase() === 's') saveCanvas();
  if (event.key.toLowerCase() === 'c') clearCanvas();
  if (event.key === '+' || event.key === '=') brushSize = Math.min(40, brushSize + 2);
  if (event.key === '-') brushSize = Math.max(2, brushSize - 2);
});
window.addEventListener('resize', sizeCanvases);
