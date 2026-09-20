import { ref } from 'vue';
import { defineStore } from 'pinia';

export const useStatusStore = defineStore(
    'account', 
    () => {
        const isLoggedIn = ref<boolean>(false);

        function resetIsLoggedIn(): void {
            isLoggedIn.value = false;
        }

        function reset(): void {
            resetIsLoggedIn();
        }

        return {
            isLoggedIn,
            resetIsLoggedIn,
            reset
        }
    }
)
