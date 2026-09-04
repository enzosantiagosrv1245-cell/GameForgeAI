export class HUD {
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
