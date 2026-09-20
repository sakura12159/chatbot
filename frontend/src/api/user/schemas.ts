import { z } from 'zod';

export const UserSchema = z.object({
    id: z.uuid(),
    name: z.string(),
    createdAt: z.iso.datetime({ offset: true, precision: 6 })
})

export const BalanceInfoSchema = z.object({
    isAvailable: z.boolean(),
    currency: z.string(),
    totalBalance: z.string()
})

export type User = z.infer<typeof UserSchema>;
export type BalanceInfo = z.infer<typeof BalanceInfoSchema>;
