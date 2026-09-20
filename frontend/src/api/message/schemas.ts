import { z } from 'zod';

export const ChatMessageSchema = z.object({
    id: z.uuid(),
    sessionId: z.uuid(),
    type: z.string(),
    role: z.string(),
    content: z.string(),
    createdAt: z.iso.datetime({ offset: true, precision: 6 }),
    reasoningContent: z.string().nullable(),
    reasoningTime: z.float32().nullable(),
    isCompressed: z.boolean()
})

export type ChatMessage = z.infer<typeof ChatMessageSchema>;
