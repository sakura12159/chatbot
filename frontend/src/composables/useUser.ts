import { ref } from 'vue';

const userId = ref<string>();
const userName = ref<string>();
const balanceMessage = ref<string>();

export const useUser = () => {

    const resetUserId = (): void => {
        userId.value = undefined;
    }

    const resetUserName = (): void => {
        userName.value = undefined;
    }

    const resetBalanceMessage = (): void => {
        balanceMessage.value = undefined;
    }

    const reset = (): void => {
        resetUserId();
        resetUserName();
        resetBalanceMessage();
    }
    return {
        userId,
        userName,
        balanceMessage,
        resetUserId,
        resetUserName,
        resetBalanceMessage,
        reset
    }
}
