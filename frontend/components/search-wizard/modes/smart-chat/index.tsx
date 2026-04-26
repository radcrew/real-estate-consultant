"use client";

import { ChatPanel } from "./chat-panel";
import { SmartChatProvider } from "@contexts/smart-chat";
import { SidePanel } from "./side-panel";
import { styles } from "./styles";

export const SmartChat = () => (
  <SmartChatProvider>
    <div className={styles.layout}>
      <ChatPanel />
      <SidePanel />
    </div>
  </SmartChatProvider>
);
