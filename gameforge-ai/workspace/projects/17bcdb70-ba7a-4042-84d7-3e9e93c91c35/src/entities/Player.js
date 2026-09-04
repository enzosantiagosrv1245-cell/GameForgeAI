export class Player {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.w = 32;
    this.h = 32;
    this.speed = 200;
    this.maxHealth = 100;
    this.health = 100;
    this.facing = 'down';
    this.sprite = null;
  }

  setSprite(image) {
    this.sprite = image;
  }

  update(dt, input, mapWidth, mapHeight, obstacles) {
    const move = input.getMovementVector();
    if (move.x !== 0 || move.y !== 0) {
      this.facing = Math.abs(move.x) > Math.abs(move.y)
        ? (move.x > 0 ? 'right' : 'left')
        : (move.y > 0 ? 'down' : 'up');
    }
    this.x += move.x * this.speed * dt;
    this.y += move.y * this.speed * dt;

    this.x = Math.max(0, Math.min(this.x, mapWidth - this.w));
    this.y = Math.max(0, Math.min(this.y, mapHeight - this.h));
  }

  takeDamage(amount) {
    this.health = Math.max(0, this.health - amount);
    return this.health <= 0;
  }

  heal(amount) {
    this.health = Math.min(this.maxHealth, this.health + amount);
  }

  render(renderer, camera) {
    if (this.sprite) {
      renderer.drawSprite(this.sprite, this.x, this.y, this.w, this.h, camera);
    } else {
      renderer.drawRect(this.x, this.y, this.w, this.h, '#4ea1ff', camera);
    }
  }
}
