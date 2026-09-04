export const GameStates = Object.freeze({
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
