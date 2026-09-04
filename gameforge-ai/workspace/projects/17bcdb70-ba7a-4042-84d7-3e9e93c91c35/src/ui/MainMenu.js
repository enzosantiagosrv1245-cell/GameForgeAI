export class MainMenu {
  constructor(rootElement, onStart) {
    this.root = rootElement;
    this.onStart = onStart;
  }

  show() {
    this.root.innerHTML = `
      <div style="position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0b0b0fee;color:#eaeaea;font-family:sans-serif;pointer-events:all;">
        <h1 style="font-size:2.5rem;margin-bottom:1rem;">Novo Jogo</h1>
        <button id="btn-start" style="padding:12px 32px;font-size:1.1rem;background:#4ea1ff;border:none;border-radius:6px;color:#0b0b0f;cursor:pointer;">Iniciar Jogo</button>
      </div>
    `;
    this.root.querySelector('#btn-start').addEventListener('click', () => {
      this.hide();
      this.onStart();
    });
  }

  hide() {
    this.root.innerHTML = '';
  }
}
