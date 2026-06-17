// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AgentView } from "@components/agents/view";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: () => false, toggle: vi.fn() }),
}));

const mockGetAgent = vi.fn();
vi.mock("@services/listings", () => ({
  listingsService: { getAgent: (...a: unknown[]) => mockGetAgent(...a) },
}));

beforeEach(() => vi.clearAllMocks());

describe("AgentView", () => {
  it("shows loading state initially", () => {
    mockGetAgent.mockReturnValue(new Promise(() => {}));
    render(<AgentView broker="Jane Broker" />);
    expect(screen.getByText(/loading agent/i)).toBeInTheDocument();
  });

  it("shows error notice on failure", async () => {
    mockGetAgent.mockRejectedValue(new Error("Not found"));
    render(<AgentView broker="Jane Broker" />);
    await waitFor(() => expect(screen.queryByText(/loading agent/i)).not.toBeInTheDocument());
    expect(screen.getByText(/request failed/i)).toBeInTheDocument();
  });

  it("renders agent name after load", async () => {
    mockGetAgent.mockResolvedValue({ name: "Jane Broker", email: "jane@broker.com", phone: null, properties: [] });
    render(<AgentView broker="Jane Broker" />);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Jane Broker" })).toBeInTheDocument());
  });

  it("renders agent email link", async () => {
    mockGetAgent.mockResolvedValue({ name: "Jane Broker", email: "jane@broker.com", phone: null, properties: [] });
    render(<AgentView broker="Jane Broker" />);
    await waitFor(() => expect(screen.getByRole("link", { name: "jane@broker.com" })).toHaveAttribute("href", "mailto:jane@broker.com"));
  });

  it("shows no-listings notice when agent has none", async () => {
    mockGetAgent.mockResolvedValue({ name: "Jane Broker", email: null, phone: null, properties: [] });
    render(<AgentView broker="Jane Broker" />);
    await waitFor(() => expect(screen.getByText(/no active listings/i)).toBeInTheDocument());
  });
});
