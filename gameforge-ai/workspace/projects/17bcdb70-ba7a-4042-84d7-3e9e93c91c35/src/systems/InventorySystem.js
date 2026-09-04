export class InventorySystem {
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
