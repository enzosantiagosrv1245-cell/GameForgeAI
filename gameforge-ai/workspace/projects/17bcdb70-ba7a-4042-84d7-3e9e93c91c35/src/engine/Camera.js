export class Camera {
  constructor(viewWidth, viewHeight, mapWidth, mapHeight) {
    this.x = 0;
    this.y = 0;
    this.viewWidth = viewWidth;
    this.viewHeight = viewHeight;
    this.mapWidth = mapWidth;
    this.mapHeight = mapHeight;
  }

  follow(targetX, targetY) {
    this.x = targetX - this.viewWidth / 2;
    this.y = targetY - this.viewHeight / 2;

    this.x = Math.max(0, Math.min(this.x, Math.max(0, this.mapWidth - this.viewWidth)));
    this.y = Math.max(0, Math.min(this.y, Math.max(0, this.mapHeight - this.viewHeight)));
  }
}
