export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  clear(color = '#1a1a22') {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  drawRect(x, y, w, h, color, camera) {
    const sx = x - (camera ? camera.x : 0);
    const sy = y - (camera ? camera.y : 0);
    this.ctx.fillStyle = color;
    this.ctx.fillRect(sx, sy, w, h);
  }

  drawCircle(x, y, r, color, camera) {
    const sx = x - (camera ? camera.x : 0);
    const sy = y - (camera ? camera.y : 0);
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(sx, sy, r, 0, Math.PI * 2);
    this.ctx.fill();
  }

  drawSprite(image, x, y, w, h, camera) {
    if (!image || !image.complete) return;
    const sx = x - (camera ? camera.x : 0);
    const sy = y - (camera ? camera.y : 0);
    this.ctx.drawImage(image, sx, sy, w, h);
  }

  drawText(text, x, y, options = {}) {
    this.ctx.fillStyle = options.color || '#eaeaea';
    this.ctx.font = options.font || '14px sans-serif';
    this.ctx.fillText(text, x, y);
  }
}
