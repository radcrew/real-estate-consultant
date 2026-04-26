"use client";

import { useState } from "react";

import type { LlmInputResponse } from "@services/intake-sessions";

import { ChatPanel } from "./chat-panel";
import { SidePanel } from "./side-panel";
import { styles } from "./styles";

export const SmartChat = () => {
  const [lastResponse, setLastResponse] = useState<LlmInputResponse | null>(null);

  return (
    <div className={styles.layout}>
      <ChatPanel onLlmSuccess={setLastResponse} />
      <SidePanel lastResponse={lastResponse} />
    </div>
  );
};
