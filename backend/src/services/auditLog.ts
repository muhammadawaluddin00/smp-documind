/**
 * Audit Logger
 * ------------
 * Appends one line per Q&A interaction to an audit file. Required by
 * the data privacy policy (DOC-003) and the GenAI usage guidelines
 * (DOC-004) so that every model-generated answer can be reconstructed
 * and reviewed.
 *
 * In production, this would write to a queue (e.g. Kafka, SQS) feeding
 * a centralised log store. For this project we use a local newline-
 * delimited JSON file.
 */

import { promises as fs } from 'node:fs';
import path from 'node:path';
import { AuditLogEntry } from '../types';

const AUDIT_LOG_PATH =
  process.env.AUDIT_LOG_PATH ?? path.resolve(process.cwd(), 'audit.log');

async function appendLine(entry: AuditLogEntry): Promise<void> {
  await fs.appendFile(
    AUDIT_LOG_PATH,
    JSON.stringify(entry) + '\n',
    'utf-8',
  );
}

export const auditLog = {
  async record(entry: AuditLogEntry): Promise<void> {
    try {
      await appendLine(entry);
    } catch (err) {
      // Audit logging failure should never block a user response, but
      // we surface it loudly so it gets noticed.
      console.error('[audit] failed to write entry', err);
    }
  },
};
