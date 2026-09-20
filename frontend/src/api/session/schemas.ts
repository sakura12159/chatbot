import { z } from 'zod';
import { ChatMessageSchema } from '@/api/message/schemas';

const ChatSessionInfoSchema = z.object({
    id: z.uuid(),
    title: z.string(),
    totalTokens: z.int().min(0)
})

export const ChatSessionInfoListSchema = z.object({
    userId: z.uuid(),
    sessions: z.array(ChatSessionInfoSchema)
})

export const ChatSessionSchema = z.object({
    id: z.uuid(),
    userId: z.uuid(),
    title: z.string(),
    totalTokens: z.int().min(0),
    createdAt: z.iso.datetime({ offset: true, precision: 6 }),
    messages: z.array(ChatMessageSchema)
})

export type ChatSessionInfoList = z.infer<typeof ChatSessionInfoListSchema>;
export type ChatSession = z.infer<typeof ChatSessionSchema>;
