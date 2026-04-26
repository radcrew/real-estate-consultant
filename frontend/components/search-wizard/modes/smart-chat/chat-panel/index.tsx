"use client";

import { Bot, Loader2 } from "lucide-react";

import { ChatComposer } from "./chat-composer";
import { useSmartChat } from "@contexts/smart-chat";
import { MessageList } from "./message-list";
import { styles } from "../styles";

export const ChatPanel = () => {
  const {
    busyBootstrap,
    draft,
    errorMessage,
    handleSend,
    isSending,
    messages,
    sessionId,
    setDraft,
    textareaRef,
  } = useSmartChat();

  return (
    <div className={styles.chatColumn}>
      <header className={styles.chatHeader}>
        <div className={styles.avatarBot}>
          <Bot className="size-4" aria-hidden />
        </div>
        <h2 className={styles.chatTitle}>AI Property Assistant</h2>
      </header>

      {errorMessage && (
        <div className={`${styles.errorBanner} mx-4 mt-3 sm:mx-5`}>{errorMessage}</div>
      )}

      {busyBootstrap ? (
        <div className={styles.loadingWrap}>
          <Loader2 className="mr-2 size-5 animate-spin" aria-hidden />
          Connecting…
        </div>
      ) : (
        <>
          <MessageList messages={messages} isSending={isSending} />
          <ChatComposer
            draft={draft}
            setDraft={setDraft}
            textareaRef={textareaRef}
            sessionId={sessionId}
            isSending={isSending}
            onSend={() => void handleSend()}
          />
        </>
      )}
    </div>
  );
};
