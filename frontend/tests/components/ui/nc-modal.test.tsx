// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NcModal } from "@components/ui/nc-modal";

describe("NcModal", () => {
  it("renders the default trigger button", () => {
    render(<NcModal renderContent={() => <p>Content</p>} />);
    expect(screen.getByRole("button", { name: /open modal/i })).toBeInTheDocument();
  });

  it("uses a custom renderTrigger", () => {
    render(
      <NcModal
        renderContent={() => <p>Content</p>}
        renderTrigger={(open) => <button onClick={open}>Custom trigger</button>}
      />,
    );
    expect(screen.getByRole("button", { name: "Custom trigger" })).toBeInTheDocument();
  });

  it("opens and shows content when trigger is clicked", async () => {
    render(
      <NcModal renderContent={() => <p>Modal body</p>} modalTitle="My Modal" />,
    );
    await userEvent.click(screen.getByRole("button", { name: /open modal/i }));
    expect(screen.getByText("Modal body")).toBeInTheDocument();
    expect(screen.getByText("My Modal")).toBeInTheDocument();
  });

  it("calls onCloseModal when close button is clicked", async () => {
    const onClose = vi.fn();
    render(<NcModal renderContent={() => <p>Content</p>} onCloseModal={onClose} />);
    await userEvent.click(screen.getByRole("button", { name: /open modal/i }));
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("renders as open when isOpenProp is true", () => {
    render(
      <NcModal renderContent={() => <p>Controlled content</p>} isOpenProp modalTitle="Title" />,
    );
    expect(screen.getByText("Controlled content")).toBeInTheDocument();
  });
});
