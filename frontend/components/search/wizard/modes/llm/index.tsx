"use client";

import { useState } from "react";

import type { LlmInputResponse } from "@services/intake-sessions";

import { ChatPanel } from "./panels/chat";
import { SidePanel } from "./panels/side";
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
