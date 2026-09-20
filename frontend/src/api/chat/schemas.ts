import { z } from 'zod';

export const ChatRequestParamsSchema = z.object({
    sessionId: z.uuid(),
    thinking: z.boolean(),
    web: z.boolean(),
    regenerate: z.boolean()
})

export const ChatResponseChunkSchema = z.object({
    sessionId: z.uuid(),
    type: z.string(),
    content: z.string().nullable(),
    reasoningContent: z.string().nullable(),
    reasoningTime: z.float32().nullable(),
    done: z.boolean()
})

export type ChatRequestParams = z.infer<typeof ChatRequestParamsSchema>;
export type ChatResponseChunk = z.infer<typeof ChatResponseChunkSchema>;
