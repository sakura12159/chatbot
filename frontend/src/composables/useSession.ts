import { ref } from 'vue';
import { listSessions } from '@/api/user';
import { type ChatSessionInfoList } from '@/api/session/schemas';

const sessionId = ref<string>();
const title = ref<string>('New Session');
const tokenUsage = ref<number>(0);
const sessionList = ref<ChatSessionInfoList>();

export const useSession = () => {

    const loadSessionList = async (userId: string): Promise<void> => {
        sessionList.value = await listSessions(userId);
    }

    const resetSessionId = (): void => {
        sessionId.value = undefined;
    }

    const resetTitle = (): void => {
        title.value = 'New Session';
    }

    const resetTokenUsage = (): void => {
        tokenUsage.value = 0;
    }

    const resetSessionList = (): void => {
        sessionList.value = undefined;
    }

    const reset = (): void => {
        resetSessionId();
        resetTitle();
        resetTokenUsage();
        resetSessionList();
    }

    return {
        sessionId,
        title,
        tokenUsage,
        sessionList,
        loadSessionList,
        resetSessionId,
        resetTitle,
        resetTokenUsage,
        resetSessionList,
        reset
    }
}
