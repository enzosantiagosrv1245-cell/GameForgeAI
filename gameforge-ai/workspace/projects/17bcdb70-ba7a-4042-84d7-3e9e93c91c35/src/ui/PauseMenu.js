export class PauseMenu {
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
