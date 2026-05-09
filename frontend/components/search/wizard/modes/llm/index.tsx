"use client";

import { useState } from "react";

import type { LlmInputResponse } from "@services/intake-sessions";

import { ChatPanel } from "./panels/chat";
import { SidePanel } from "./panels/side";
import { STYLES } from "./styles";

export const SmartChat = () => {
  const [lastResponse, setLastResponse] = useState<LlmInputResponse | null>(null);

  return (
    <div className={STYLES.layout}>
      <ChatPanel onLlmSuccess={setLastResponse} />
      <SidePanel lastResponse={lastResponse} />
    </div>
  );
};
