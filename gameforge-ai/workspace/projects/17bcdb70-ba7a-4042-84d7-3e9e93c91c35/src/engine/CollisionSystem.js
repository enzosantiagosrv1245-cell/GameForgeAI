export class CollisionSystem {
  static aabbIntersects(a, b) {
    return (
      a.x < b.x + b.w &&
      a.x + a.w > b.x &&
      a.y < b.y + b.h &&
      a.y + a.h > b.y
    );
  }

  static clampToBounds(entity, mapWidth, mapHeight) {
    entity.x = Math.max(0, Math.min(entity.x, mapWidth - entity.w));
    entity.y = Math.max(0, Math.min(entity.y, mapHeight - entity.h));
  }

  static resolveEntityCollisions(entity, obstacles) {
    for (const obstacle of obstacles) {
      if (CollisionSystem.aabbIntersects(entity, obstacle)) {
        const overlapX = Math.min(
          entity.x + entity.w - obstacle.x,
          obstacle.x + obstacle.w - entity.x
        );
        const overlapY = Math.min(
          entity.y + entity.h - obstacle.y,
          obstacle.y + obstacle.h - entity.y
        );
        if (overlapX < overlapY) {
          entity.x += entity.x < obstacle.x ? -overlapX : overlapX;
        } else {
          entity.y += entity.y < obstacle.y ? -overlapY : overlapY;
        }
      }
    }
  }
}
