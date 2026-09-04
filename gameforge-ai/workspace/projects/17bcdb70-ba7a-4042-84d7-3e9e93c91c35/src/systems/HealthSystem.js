export class HealthSystem {
  static isDead(entity) {
    return entity.health <= 0;
  }

  static percentage(entity) {
    return Math.max(0, Math.min(1, entity.health / entity.maxHealth));
  }
}
