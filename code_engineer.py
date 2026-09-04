"""
CodeEngineer (item 11 da especificação).

Gera código-fonte REAL e funcional (não pseudocódigo, sem `pass`/TODO)
para o jogo alvo (HTML5 Canvas + JavaScript vanilla). Cada método
retorna um arquivo completo e executável, com base na design_spec e
architecture produzidas por GameDesigner/GameArchitect.
"""
from __future__ import annotations

from typing import Any


class CodeEngineer:
    """Gera os arquivos-fonte de um jogo HTML5/Canvas funcional."""

    def generate_all_files(
        self, design_spec: dict[str, Any], architecture: dict[str, Any]
    ) -> dict[str, str]:
        systems = design_spec.get("systems", [])
        files: dict[str, str] = {
            "index.html": self._index_html(design_spec),
            "src/engine/GameLoop.js": self._game_loop_js(),
            "src/engine/InputManager.js": self._input_manager_js(),
            "src/engine/Renderer.js": self._renderer_js(),
            "src/engine/Camera.js": self._camera_js(),
            "src/engine/CollisionSystem.js": self._collision_system_js(),
            "src/entities/Player.js": self._player_js(design_spec),
            "src/entities/Enemy.js": self._enemy_js(design_spec),
            "src/systems/HealthSystem.js": self._health_system_js(),
            "src/ui/HUD.js": self._hud_js(design_spec),
            "src/ui/MainMenu.js": self._main_menu_js(design_spec),
            "src/ui/PauseMenu.js": self._pause_menu_js(),
            "src/map/MapLoader.js": self._map_loader_js(design_spec),
            "src/state/GameState.js": self._game_state_js(),
            "src/main.js": self._main_js(design_spec),
        }
        if "inventory" in systems:
            files["src/systems/InventorySystem.js"] = self._inventory_system_js()
        if "hunger" in systems:
            files["src/systems/HungerSystem.js"] = self._hunger_system_js()
        if "stamina" in systems:
            files["src/systems/StaminaSystem.js"] = self._stamina_system_js()
        if "combat" in systems:
            files["src/systems/CombatSystem.js"] = self._combat_system_js()
        if "loot" in systems:
            files["src/systems/LootSystem.js"] = self._loot_system_js()
        if "economy" in systems:
            files["src/systems/EconomySystem.js"] = self._economy_system_js()
        return files

    # ------------------------------------------------------------------
    # HTML shell
    # ------------------------------------------------------------------
    def _index_html(self, design_spec: dict[str, Any]) -> str:
        name = design_spec.get("name", "Jogo GameForge")
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>{name}</title>
  <style>
    html, body {{ margin: 0; padding: 0; background: #0b0b0f; overflow: hidden; }}
    #game-canvas {{ display: block; margin: 0 auto; background: #1a1a22; image-rendering: pixelated; }}
    #hud {{ position: fixed; top: 0; left: 0; right: 0; pointer-events: none; font-family: sans-serif; }}
  </style>
</head>
<body>
  <canvas id="game-canvas" width="960" height="640"></canvas>
  <div id="hud"></div>
  <script type="module" src="./src/main.js"></script>
</body>
</html>
"""

    # ------------------------------------------------------------------
    # Engine core
    # ------------------------------------------------------------------
    def _game_loop_js(self) -> str:
        return """export class GameLoop {
  constructor(updateFn, renderFn) {
    this.updateFn = updateFn;
    this.renderFn = renderFn;
    this.lastTime = 0;
    this.running = false;
    this._frame = this._frame.bind(this);
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.lastTime = performance.now();
    requestAnimationFrame(this._frame);
  }

  stop() {
    this.running = false;
  }

  _frame(currentTime) {
    if (!this.running) return;
    const deltaMs = currentTime - this.lastTime;
    this.lastTime = currentTime;
    const dt = Math.min(deltaMs / 1000, 0.05); // clamp para evitar saltos grandes

    this.updateFn(dt);
    this.renderFn();

    requestAnimationFrame(this._frame);
  }
}
"""

    def _input_manager_js(self) -> str:
        return """export class InputManager {
  constructor() {
    this.keys = new Set();
    window.addEventListener('keydown', (e) => this.keys.add(e.code));
    window.addEventListener('keyup', (e) => this.keys.delete(e.code));
  }

  isDown(code) {
    return this.keys.has(code);
  }

  getMovementVector() {
    let x = 0;
    let y = 0;
    if (this.isDown('KeyW') || this.isDown('ArrowUp')) y -= 1;
    if (this.isDown('KeyS') || this.isDown('ArrowDown')) y += 1;
    if (this.isDown('KeyA') || this.isDown('ArrowLeft')) x -= 1;
    if (this.isDown('KeyD') || this.isDown('ArrowRight')) x += 1;

    const length = Math.hypot(x, y);
    if (length > 0) {
      x /= length;
      y /= length;
    }
    return { x, y };
  }
}
"""

    def _renderer_js(self) -> str:
        return """export class Renderer {
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
"""

    def _camera_js(self) -> str:
        return """export class Camera {
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
"""

    def _collision_system_js(self) -> str:
        return """export class CollisionSystem {
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
"""

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------
    def _player_js(self, design_spec: dict[str, Any]) -> str:
        max_health = design_spec.get("player", {}).get("health", 100)
        speed = design_spec.get("player", {}).get("speed", 200)
        return f"""export class Player {{
  constructor(x, y) {{
    this.x = x;
    this.y = y;
    this.w = 32;
    this.h = 32;
    this.speed = {speed};
    this.maxHealth = {max_health};
    this.health = {max_health};
    this.facing = 'down';
    this.sprite = null;
  }}

  setSprite(image) {{
    this.sprite = image;
  }}

  update(dt, input, mapWidth, mapHeight, obstacles) {{
    const move = input.getMovementVector();
    if (move.x !== 0 || move.y !== 0) {{
      this.facing = Math.abs(move.x) > Math.abs(move.y)
        ? (move.x > 0 ? 'right' : 'left')
        : (move.y > 0 ? 'down' : 'up');
    }}
    this.x += move.x * this.speed * dt;
    this.y += move.y * this.speed * dt;

    this.x = Math.max(0, Math.min(this.x, mapWidth - this.w));
    this.y = Math.max(0, Math.min(this.y, mapHeight - this.h));
  }}

  takeDamage(amount) {{
    this.health = Math.max(0, this.health - amount);
    return this.health <= 0;
  }}

  heal(amount) {{
    this.health = Math.min(this.maxHealth, this.health + amount);
  }}

  render(renderer, camera) {{
    if (this.sprite) {{
      renderer.drawSprite(this.sprite, this.x, this.y, this.w, this.h, camera);
    }} else {{
      renderer.drawRect(this.x, this.y, this.w, this.h, '#4ea1ff', camera);
    }}
  }}
}}
"""

    def _enemy_js(self, design_spec: dict[str, Any]) -> str:
        enemies = design_spec.get("enemies", [])
        default_health = enemies[0]["health"] if enemies else 30
        default_damage = enemies[0]["damage"] if enemies else 5
        return f"""export class Enemy {{
  constructor(x, y, options = {{}}) {{
    this.x = x;
    this.y = y;
    this.w = 28;
    this.h = 28;
    this.health = options.health ?? {default_health};
    this.maxHealth = this.health;
    this.damage = options.damage ?? {default_damage};
    this.speed = options.speed ?? 80;
    this.attackCooldown = 0;
    this.sprite = null;
  }}

  setSprite(image) {{
    this.sprite = image;
  }}

  update(dt, target) {{
    const dx = target.x - this.x;
    const dy = target.y - this.y;
    const dist = Math.hypot(dx, dy);
    if (dist > 1) {{
      this.x += (dx / dist) * this.speed * dt;
      this.y += (dy / dist) * this.speed * dt;
    }}
    if (this.attackCooldown > 0) {{
      this.attackCooldown -= dt;
    }}
  }}

  canAttack() {{
    return this.attackCooldown <= 0;
  }}

  triggerAttackCooldown() {{
    this.attackCooldown = 1.0;
  }}

  takeDamage(amount) {{
    this.health = Math.max(0, this.health - amount);
    return this.health <= 0;
  }}

  render(renderer, camera) {{
    if (this.sprite) {{
      renderer.drawSprite(this.sprite, this.x, this.y, this.w, this.h, camera);
    }} else {{
      renderer.drawRect(this.x, this.y, this.w, this.h, '#c0392b', camera);
    }}
  }}
}}
"""

    # ------------------------------------------------------------------
    # Systems
    # ------------------------------------------------------------------
    def _health_system_js(self) -> str:
        return """export class HealthSystem {
  static isDead(entity) {
    return entity.health <= 0;
  }

  static percentage(entity) {
    return Math.max(0, Math.min(1, entity.health / entity.maxHealth));
  }
}
"""

    def _inventory_system_js(self) -> str:
        return """export class InventorySystem {
  constructor(maxSlots = 12) {
    this.maxSlots = maxSlots;
    this.items = [];
  }

  addItem(item) {
    if (this.items.length >= this.maxSlots) {
      return false;
    }
    this.items.push(item);
    return true;
  }

  removeItem(itemId) {
    const index = this.items.findIndex((i) => i.id === itemId);
    if (index === -1) return null;
    return this.items.splice(index, 1)[0];
  }

  hasSpace() {
    return this.items.length < this.maxSlots;
  }

  getItems() {
    return [...this.items];
  }
}
"""

    def _hunger_system_js(self) -> str:
        return """export class HungerSystem {
  constructor(maxHunger = 100, decayPerSecond = 0.5) {
    this.maxHunger = maxHunger;
    this.hunger = maxHunger;
    this.decayPerSecond = decayPerSecond;
  }

  update(dt, player) {
    this.hunger = Math.max(0, this.hunger - this.decayPerSecond * dt);
    if (this.hunger <= 0) {
      player.takeDamage(1 * dt);
    }
  }

  feed(amount) {
    this.hunger = Math.min(this.maxHunger, this.hunger + amount);
  }

  percentage() {
    return this.hunger / this.maxHunger;
  }
}
"""

    def _stamina_system_js(self) -> str:
        return """export class StaminaSystem {
  constructor(maxStamina = 100, regenPerSecond = 10, drainPerSecond = 25) {
    this.maxStamina = maxStamina;
    this.stamina = maxStamina;
    this.regenPerSecond = regenPerSecond;
    this.drainPerSecond = drainPerSecond;
  }

  update(dt, isSprinting) {
    if (isSprinting && this.stamina > 0) {
      this.stamina = Math.max(0, this.stamina - this.drainPerSecond * dt);
    } else {
      this.stamina = Math.min(this.maxStamina, this.stamina + this.regenPerSecond * dt);
    }
  }

  canSprint() {
    return this.stamina > 0;
  }

  percentage() {
    return this.stamina / this.maxStamina;
  }
}
"""

    def _combat_system_js(self) -> str:
        return """export class CombatSystem {
  constructor() {
    this.playerAttackCooldown = 0;
    this.playerDamage = 15;
    this.attackRange = 40;
  }

  update(dt) {
    if (this.playerAttackCooldown > 0) {
      this.playerAttackCooldown -= dt;
    }
  }

  tryPlayerAttack(player, enemies) {
    if (this.playerAttackCooldown > 0) return [];

    this.playerAttackCooldown = 0.4;
    const defeated = [];

    for (const enemy of enemies) {
      const dx = enemy.x - player.x;
      const dy = enemy.y - player.y;
      const dist = Math.hypot(dx, dy);
      if (dist <= this.attackRange) {
        const isDead = enemy.takeDamage(this.playerDamage);
        if (isDead) defeated.push(enemy);
      }
    }
    return defeated;
  }

  tryEnemyAttack(enemy, player) {
    const dx = player.x - enemy.x;
    const dy = player.y - enemy.y;
    const dist = Math.hypot(dx, dy);
    if (dist <= 36 && enemy.canAttack()) {
      enemy.triggerAttackCooldown();
      return player.takeDamage(enemy.damage);
    }
    return false;
  }
}
"""

    def _loot_system_js(self) -> str:
        return """export class LootSystem {
  constructor(lootTable = null) {
    this.lootTable = lootTable || [
      { id: 'ammo', name: 'Munição', chance: 0.4 },
      { id: 'food', name: 'Comida', chance: 0.3 },
      { id: 'medkit', name: 'Kit Médico', chance: 0.15 },
    ];
  }

  rollLoot() {
    const drops = [];
    for (const entry of this.lootTable) {
      if (Math.random() < entry.chance) {
        drops.push({ id: entry.id, name: entry.name });
      }
    }
    return drops;
  }
}
"""

    def _economy_system_js(self) -> str:
        return """export class EconomySystem {
  constructor(startingCurrency = 0) {
    this.currency = startingCurrency;
  }

  addCurrency(amount) {
    this.currency += amount;
  }

  spend(amount) {
    if (this.currency < amount) return false;
    this.currency -= amount;
    return true;
  }
}
"""

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _hud_js(self, design_spec: dict[str, Any]) -> str:
        return """export class HUD {
  constructor(rootElement) {
    this.root = rootElement;
    this.root.innerHTML = `
      <div style="position:fixed;top:12px;left:12px;font-family:sans-serif;color:#eaeaea;">
        <div style="width:180px;height:14px;background:#222;border:1px solid #444;border-radius:4px;overflow:hidden;margin-bottom:4px;">
          <div id="hud-health" style="width:100%;height:100%;background:#e74c3c;"></div>
        </div>
        <div id="hud-extra"></div>
      </div>
    `;
    this.healthBar = this.root.querySelector('#hud-health');
    this.extra = this.root.querySelector('#hud-extra');
  }

  update(player, extras = {}) {
    const pct = Math.max(0, Math.min(1, player.health / player.maxHealth)) * 100;
    this.healthBar.style.width = pct + '%';

    let extraHtml = '';
    if (extras.hunger !== undefined) {
      extraHtml += `<div style="font-size:12px;">Fome: ${Math.round(extras.hunger * 100)}%</div>`;
    }
    if (extras.stamina !== undefined) {
      extraHtml += `<div style="font-size:12px;">Stamina: ${Math.round(extras.stamina * 100)}%</div>`;
    }
    if (extras.currency !== undefined) {
      extraHtml += `<div style="font-size:12px;">Moedas: ${extras.currency}</div>`;
    }
    this.extra.innerHTML = extraHtml;
  }
}
"""

    def _main_menu_js(self, design_spec: dict[str, Any]) -> str:
        name = design_spec.get("name", "Jogo")
        return f"""export class MainMenu {{
  constructor(rootElement, onStart) {{
    this.root = rootElement;
    this.onStart = onStart;
  }}

  show() {{
    this.root.innerHTML = `
      <div style="position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0b0b0fee;color:#eaeaea;font-family:sans-serif;pointer-events:all;">
        <h1 style="font-size:2.5rem;margin-bottom:1rem;">{name}</h1>
        <button id="btn-start" style="padding:12px 32px;font-size:1.1rem;background:#4ea1ff;border:none;border-radius:6px;color:#0b0b0f;cursor:pointer;">Iniciar Jogo</button>
      </div>
    `;
    this.root.querySelector('#btn-start').addEventListener('click', () => {{
      this.hide();
      this.onStart();
    }});
  }}

  hide() {{
    this.root.innerHTML = '';
  }}
}}
"""

    def _pause_menu_js(self) -> str:
        return """export class PauseMenu {
  constructor(rootElement, onResume) {
    this.root = rootElement;
    this.onResume = onResume;
    this.visible = false;
  }

  toggle() {
    this.visible ? this.hide() : this.show();
  }

  show() {
    this.visible = true;
    this.root.innerHTML = `
      <div style="position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0b0b0fcc;color:#eaeaea;font-family:sans-serif;pointer-events:all;">
        <h2>Pausado</h2>
        <button id="btn-resume" style="padding:10px 24px;background:#4ea1ff;border:none;border-radius:6px;cursor:pointer;">Continuar</button>
      </div>
    `;
    this.root.querySelector('#btn-resume').addEventListener('click', () => {
      this.hide();
      this.onResume();
    });
  }

  hide() {
    this.visible = false;
    this.root.innerHTML = '';
  }
}
"""

    # ------------------------------------------------------------------
    # Map / State / Main
    # ------------------------------------------------------------------
    def _map_loader_js(self, design_spec: dict[str, Any]) -> str:
        return """export class MapLoader {
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
"""

    def _game_state_js(self) -> str:
        return """export const GameStates = Object.freeze({
  MENU: 'menu',
  PLAYING: 'playing',
  PAUSED: 'paused',
  GAME_OVER: 'game_over',
});

export class GameState {
  constructor() {
    this.current = GameStates.MENU;
  }

  set(state) {
    this.current = state;
  }

  is(state) {
    return this.current === state;
  }
}
"""

    def _main_js(self, design_spec: dict[str, Any]) -> str:
        systems = design_spec.get("systems", [])
        has_hunger = "hunger" in systems
        has_stamina = "stamina" in systems
        has_combat = "combat" in systems
        has_economy = "economy" in systems

        extra_imports = []
        extra_init = []
        extra_update = []
        extra_hud = []

        if has_hunger:
            extra_imports.append("import { HungerSystem } from './systems/HungerSystem.js';")
            extra_init.append("const hungerSystem = new HungerSystem();")
            extra_update.append("hungerSystem.update(dt, player);")
            extra_hud.append("hunger: hungerSystem.percentage(),")

        if has_stamina:
            extra_imports.append("import { StaminaSystem } from './systems/StaminaSystem.js';")
            extra_init.append("const staminaSystem = new StaminaSystem();")
            extra_update.append("staminaSystem.update(dt, input.isDown('ShiftLeft'));")
            extra_hud.append("stamina: staminaSystem.percentage(),")

        if has_combat:
            extra_imports.append("import { CombatSystem } from './systems/CombatSystem.js';")
            extra_init.append("const combatSystem = new CombatSystem();")
            extra_update.append(
                "combatSystem.update(dt);\n"
                "    if (input.isDown('Space')) { combatSystem.tryPlayerAttack(player, enemies); }"
            )

        if has_economy:
            extra_imports.append("import { EconomySystem } from './systems/EconomySystem.js';")
            extra_init.append("const economySystem = new EconomySystem();")
            extra_hud.append("currency: economySystem.currency,")

        imports_block = "\n".join(extra_imports)
        init_block = "\n  ".join(extra_init)
        update_block = "\n    ".join(extra_update)
        hud_block = "\n      ".join(extra_hud)

        return f"""import {{ GameLoop }} from './engine/GameLoop.js';
import {{ InputManager }} from './engine/InputManager.js';
import {{ Renderer }} from './engine/Renderer.js';
import {{ Camera }} from './engine/Camera.js';
import {{ CollisionSystem }} from './engine/CollisionSystem.js';
import {{ Player }} from './entities/Player.js';
import {{ Enemy }} from './entities/Enemy.js';
import {{ HUD }} from './ui/HUD.js';
import {{ MainMenu }} from './ui/MainMenu.js';
import {{ PauseMenu }} from './ui/PauseMenu.js';
import {{ MapLoader }} from './map/MapLoader.js';
import {{ GameState, GameStates }} from './state/GameState.js';
{imports_block}

const canvas = document.getElementById('game-canvas');
const hudRoot = document.getElementById('hud');

const renderer = new Renderer(canvas);
const input = new InputManager();
const map = new MapLoader();
const gameState = new GameState();

const spawn = map.getSpawnPoint();
const player = new Player(spawn.x, spawn.y);
const camera = new Camera(canvas.width, canvas.height, map.width, map.height);
const hud = new HUD(hudRoot);

let enemies = [];
function spawnEnemies(count) {{
  enemies = [];
  for (let i = 0; i < count; i++) {{
    enemies.push(new Enemy(Math.random() * map.width, Math.random() * map.height));
  }}
}}
spawnEnemies(6);

{init_block}

const mainMenu = new MainMenu(hudRoot, () => {{
  gameState.set(GameStates.PLAYING);
}});

const pauseMenu = new PauseMenu(hudRoot, () => {{
  gameState.set(GameStates.PLAYING);
}});

window.addEventListener('keydown', (e) => {{
  if (e.code === 'Escape' && gameState.is(GameStates.PLAYING)) {{
    gameState.set(GameStates.PAUSED);
    pauseMenu.show();
  }} else if (e.code === 'Escape' && gameState.is(GameStates.PAUSED)) {{
    gameState.set(GameStates.PLAYING);
    pauseMenu.hide();
  }}
}});

function update(dt) {{
  if (!gameState.is(GameStates.PLAYING)) return;

  player.update(dt, input, map.width, map.height, map.obstacles);
  CollisionSystem.resolveEntityCollisions(player, map.obstacles);
  camera.follow(player.x + player.w / 2, player.y + player.h / 2);

  for (const enemy of enemies) {{
    enemy.update(dt, player);
  }}

  {update_block}

  if (player.health <= 0) {{
    gameState.set(GameStates.GAME_OVER);
  }}

  hud.update(player, {{ {hud_block} }});
}}

function render() {{
  renderer.clear();
  map.render(renderer, camera);
  for (const enemy of enemies) {{
    enemy.render(renderer, camera);
  }}
  player.render(renderer, camera);

  if (gameState.is(GameStates.GAME_OVER)) {{
    renderer.drawText('GAME OVER', canvas.width / 2 - 60, canvas.height / 2, {{ font: '32px sans-serif', color: '#e74c3c' }});
  }}
}}

const loop = new GameLoop(update, render);
loop.start();
mainMenu.show();
"""