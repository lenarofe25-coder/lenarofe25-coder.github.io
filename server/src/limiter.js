// Limiteur de débit par adresse IP (un petit Durable Object par IP, fenêtre fixe).
import { DurableObject } from 'cloudflare:workers';

export class Limiter extends DurableObject {
  async hit(bucket, limit, windowMs) {
    const now = Date.now();
    const entry = (await this.ctx.storage.get(bucket)) || { start: now, count: 0 };
    if (now - entry.start >= windowMs) {
      entry.start = now;
      entry.count = 0;
    }
    entry.count += 1;
    await this.ctx.storage.put(bucket, entry);
    await this.ctx.storage.setAlarm(now + windowMs);
    return entry.count <= limit;
  }

  async alarm() {
    await this.ctx.storage.deleteAll();
  }
}
