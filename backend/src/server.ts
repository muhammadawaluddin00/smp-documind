/**
 * SMP DocuMind — Backend Server
 * ==============================
 *
 * Express server that fronts the Python ML service. Adds:
 *   - request validation (zod)
 *   - rate limiting (per IP)
 *   - structured logging (pino)
 *   - audit logging (compliance)
 *   - CORS (frontend origin)
 *
 * Environment variables:
 *   PORT                 default 4000
 *   ML_SERVICE_URL       default http://localhost:8000
 *   FRONTEND_ORIGIN      default http://localhost:3000
 *   RATE_LIMIT_PER_MIN   default 60
 *   AUDIT_LOG_PATH       default ./audit.log
 */

import 'dotenv/config';
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import pinoHttp from 'pino-http';
import pino from 'pino';

import { router } from './routes';

const PORT = Number(process.env.PORT ?? 4000);
const FRONTEND_ORIGIN = process.env.FRONTEND_ORIGIN ?? 'http://localhost:3000';
const RATE_LIMIT_PER_MIN = Number(process.env.RATE_LIMIT_PER_MIN ?? 60);

const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  // Keep production logs structured; pretty-print in dev only.
  transport:
    process.env.NODE_ENV === 'development'
      ? { target: 'pino-pretty', options: { colorize: true } }
      : undefined,
});

const app = express();

// ---- Middleware -------------------------------------------------
app.use(cors({ origin: FRONTEND_ORIGIN, credentials: false }));
app.use(express.json({ limit: '256kb' }));
app.use(pinoHttp({ logger }));

// Rate limiting: protects against runaway clients and abusive bots.
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    max: RATE_LIMIT_PER_MIN,
    standardHeaders: true,
    legacyHeaders: false,
  }),
);

// ---- Routes -----------------------------------------------------
app.use('/api', router);

app.get('/', (_req: Request, res: Response) => {
  res.json({
    name: 'SMP DocuMind Backend',
    version: '1.0.0',
    docs: '/api/health',
  });
});

// ---- Error handler (last) ---------------------------------------
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  logger.error({ err }, 'unhandled request error');
  res.status(500).json({
    error: 'internal_server_error',
    message:
      process.env.NODE_ENV === 'development' ? err.message : 'unexpected error',
  });
});

app.listen(PORT, () => {
  logger.info(
    { port: PORT, mlService: process.env.ML_SERVICE_URL ?? 'http://localhost:8000' },
    'SMP DocuMind backend listening',
  );
});
