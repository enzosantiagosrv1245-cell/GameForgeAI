import { GameLoop } from './engine/GameLoop.js';
import { InputManager } from './engine/InputManager.js';
import { Renderer } from './engine/Renderer.js';
import { Camera } from './engine/Camera.js';
import { CollisionSystem } from './engine/CollisionSystem.js';
import { Player } from './entities/Player.js';
import { Enemy } from './entities/Enemy.js';
import { HUD } from './ui/HUD.js';
import { MainMenu } from './ui/MainMenu.js';
import { PauseMenu } from './ui/PauseMenu.js';
import { MapLoader } from './map/MapLoader.js';
import { GameState, GameStates } from './state/GameState.js';


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
function spawnEnemies(count) {
  enemies = [];
  for (let i = 0; i < count; i++) {
    enemies.push(new Enemy(Math.random() * map.width, Math.random() * map.height));
  }
}
spawnEnemies(6);



const mainMenu = new MainMenu(hudRoot, () => {
  gameState.set(GameStates.PLAYING);
});

const pauseMenu = new PauseMenu(hudRoot, () => {
  gameState.set(GameStates.PLAYING);
});

window.addEventListener('keydown', (e) => {
  if (e.code === 'Escape' && gameState.is(GameStates.PLAYING)) {
    gameState.set(GameStates.PAUSED);
    pauseMenu.show();
  } else if (e.code === 'Escape' && gameState.is(GameStates.PAUSED)) {
    gameState.set(GameStates.PLAYING);
    pauseMenu.hide();
  }
});

function update(dt) {
  if (!gameState.is(GameStates.PLAYING)) return;

  player.update(dt, input, map.width, map.height, map.obstacles);
  CollisionSystem.resolveEntityCollisions(player, map.obstacles);
  camera.follow(player.x + player.w / 2, player.y + player.h / 2);

  for (const enemy of enemies) {
    enemy.update(dt, player);
  }

  

  if (player.health <= 0) {
    gameState.set(GameStates.GAME_OVER);
  }

  hud.update(player, {  });
}

function render() {
  renderer.clear();
  map.render(renderer, camera);
  for (const enemy of enemies) {
    enemy.render(renderer, camera);
  }
  player.render(renderer, camera);

  if (gameState.is(GameStates.GAME_OVER)) {
    renderer.drawText('GAME OVER', canvas.width / 2 - 60, canvas.height / 2, { font: '32px sans-serif', color: '#e74c3c' });
  }
}

const loop = new GameLoop(update, render);
loop.start();
mainMenu.show();
