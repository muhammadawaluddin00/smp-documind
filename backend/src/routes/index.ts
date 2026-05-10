/**
 * HTTP Routes
 * -----------
 * Thin handlers that validate input, call the ML service, log the
 * exchange, and return JSON. Validation uses zod for runtime safety.
 */

import { Router, Request, Response, NextFunction } from 'express';
import { randomUUID } from 'node:crypto';
import { z } from 'zod';

import { mlService } from '../services/mlService';
import { auditLog } from '../services/auditLog';

export const router = Router();

// -----------------------------------------------------------------
// POST /api/ask
// -----------------------------------------------------------------
const AskSchema = z.object({
  question: z.string().min(1).max(2000),
  topK: z.number().int().min(1).max(10).optional(),
});

router.post(
  '/ask',
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const parsed = AskSchema.safeParse(req.body);
      if (!parsed.success) {
        res.status(400).json({ error: parsed.error.flatten() });
        return;
      }

      // In production, user_id comes from the JWT subject claim.
      const userId = (req.headers['x-user-id'] as string | undefined) ?? 'anonymous';
      const requestId = (req.headers['x-request-id'] as string | undefined) ?? randomUUID();

      const startedAt = Date.now();
      const result = await mlService.ask(parsed.data.question, parsed.data.topK);
      const wallLatencyMs = Date.now() - startedAt;

      // Audit log — fire and forget
      void auditLog.record({
        timestamp: new Date().toISOString(),
        request_id: requestId,
        user_id: userId,
        question: parsed.data.question,
        answer_preview: result.answer.slice(0, 300),
        citations: result.citations.map((c) => c.doc_id),
        latency_ms: wallLatencyMs,
        used_generator: result.used_generator,
      });

      res.json({ ...result, request_id: requestId, wall_latency_ms: wallLatencyMs });
    } catch (err) {
      next(err);
    }
  },
);

// -----------------------------------------------------------------
// GET /api/documents
// -----------------------------------------------------------------
router.get(
  '/documents',
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const docs = await mlService.listDocuments();
      res.json(docs);
    } catch (err) {
      next(err);
    }
  },
);

// -----------------------------------------------------------------
// GET /api/metrics
// -----------------------------------------------------------------
router.get(
  '/metrics',
  async (_req: Request, res: Response, next: NextFunction) => {
    try {
      const metrics = await mlService.getMetrics();
      res.json(metrics);
    } catch (err) {
      next(err);
    }
  },
);

// -----------------------------------------------------------------
// GET /api/health
// -----------------------------------------------------------------
router.get(
  '/health',
  async (_req: Request, res: Response) => {
    try {
      const ml = await mlService.health();
      res.json({ status: 'ok', ml });
    } catch (err) {
      res.status(503).json({
        status: 'degraded',
        reason: err instanceof Error ? err.message : 'unknown',
      });
    }
  },
);
