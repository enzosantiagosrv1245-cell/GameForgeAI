export class MapLoader {
  constructor(width = 2000, height = 2000) {
    this.width = width;
    this.height = height;
    this.obstacles = this._generateObstacles();
  }

  _generateObstacles() {
    const obstacles = [];
    const count = 24;
    for (let i = 0; i < count; i++) {
      obstacles.push({
        x: Math.random() * (this.width - 64),
        y: Math.random() * (this.height - 64),
        w: 48 + Math.random() * 32,
        h: 48 + Math.random() * 32,
      });
    }
    return obstacles;
  }

  render(renderer, camera) {
    for (const obs of this.obstacles) {
      renderer.drawRect(obs.x, obs.y, obs.w, obs.h, '#33333d', camera);
    }
  }

  getSpawnPoint() {
    return { x: this.width / 2, y: this.height / 2 };
  }
}
