export class Enemy {
  constructor(x, y, options = {}) {
    this.x = x;
    this.y = y;
    this.w = 28;
    this.h = 28;
    this.health = options.health ?? 30;
    this.maxHealth = this.health;
    this.damage = options.damage ?? 5;
    this.speed = options.speed ?? 80;
    this.attackCooldown = 0;
    this.sprite = null;
  }

  setSprite(image) {
    this.sprite = image;
  }

  update(dt, target) {
    const dx = target.x - this.x;
    const dy = target.y - this.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 1) {
      this.x += (dx / dist) * this.speed * dt;
      this.y += (dy / dist) * this.speed * dt;
    }
    if (this.attackCooldown > 0) {
      this.attackCooldown -= dt;
    }
  }

  canAttack() {
    return this.attackCooldown <= 0;
  }

  triggerAttackCooldown() {
    this.attackCooldown = 1.0;
  }

  takeDamage(amount) {
    this.health = Math.max(0, this.health - amount);
    return this.health <= 0;
  }

  render(renderer, camera) {
    if (this.sprite) {
      renderer.drawSprite(this.sprite, this.x, this.y, this.w, this.h, camera);
    } else {
      renderer.drawRect(this.x, this.y, this.w, this.h, '#c0392b', camera);
    }
  }
}
