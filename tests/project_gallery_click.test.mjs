import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const script = readFileSync("app/static/js/project_gallery.js", "utf8");


function createEventTarget() {
    const listeners = new Map();

    return {
        addEventListener(eventName, handler) {
            listeners.set(eventName, handler);
        },
        dispatch(eventName, event) {
            listeners.get(eventName)(event);
        },
    };
}


function createGalleryHarness() {
    const track = {
        ...createEventTarget(),
        classList: { add() {}, remove() {} },
        clientWidth: 400,
        scrollLeft: 0,
        scrollWidth: 800,
        capturedPointerId: null,
        querySelector() {
            return { getBoundingClientRect: () => ({ width: 384 }) };
        },
        setPointerCapture(pointerId) {
            this.capturedPointerId = pointerId;
        },
        hasPointerCapture(pointerId) {
            return this.capturedPointerId === pointerId;
        },
        releasePointerCapture(pointerId) {
            if (this.capturedPointerId === pointerId) this.capturedPointerId = null;
        },
        scrollBy() {},
    };
    const lightbox = { ...createEventTarget(), hidden: true };
    const lightboxImage = { src: "", alt: "" };
    const lightboxCaption = { hidden: false, textContent: "" };
    const lightboxClose = { ...createEventTarget(), focus() {} };
    const lightboxPrevious = { ...createEventTarget(), hidden: false };
    const lightboxNext = { ...createEventTarget(), hidden: false };
    const thumbnailImage = { src: "/static/example.png", alt: "Example" };
    const item = {
        ...createEventTarget(),
        querySelector() {
            return thumbnailImage;
        },
        closest() {
            return { querySelector: () => null };
        },
    };
    const previousButton = { ...createEventTarget(), disabled: false };
    const nextButton = { ...createEventTarget(), disabled: false };
    const gallery = {
        querySelector(selector) {
            return new Map([
                ["[data-gallery-track]", track],
                ["[data-gallery-previous]", previousButton],
                ["[data-gallery-next]", nextButton],
                ["[data-gallery-lightbox]", lightbox],
                ["[data-lightbox-image]", lightboxImage],
                ["[data-lightbox-caption]", lightboxCaption],
                ["[data-lightbox-close]", lightboxClose],
                ["[data-lightbox-previous]", lightboxPrevious],
                ["[data-lightbox-next]", lightboxNext],
            ]).get(selector);
        },
        querySelectorAll() {
            return [item];
        },
    };
    const document = {
        ...createEventTarget(),
        activeElement: null,
        body: { classList: { add() {}, remove() {} } },
        querySelectorAll() {
            return [gallery];
        },
    };

    vm.runInNewContext(script, {
        document,
        window: { addEventListener() {} },
        getComputedStyle: () => ({ columnGap: "16px" }),
    });

    return { item, lightbox, track };
}


test("a click after no drag opens the lightbox", () => {
    const { item, lightbox, track } = createGalleryHarness();

    track.dispatch("pointerdown", { pointerType: "mouse", button: 0, pointerId: 1, clientX: 100 });
    track.dispatch("pointerup", { pointerId: 1 });
    item.dispatch("click", { preventDefault() {} });

    assert.equal(lightbox.hidden, false);
});


test("a drag over the threshold does not open the lightbox", () => {
    const { item, lightbox, track } = createGalleryHarness();
    let prevented = false;

    track.dispatch("pointerdown", { pointerType: "mouse", button: 0, pointerId: 1, clientX: 100 });
    track.dispatch("pointermove", {
        pointerId: 1,
        clientX: 92,
        preventDefault() {},
    });
    track.dispatch("pointerup", { pointerId: 1 });
    item.dispatch("click", { preventDefault() { prevented = true; } });

    assert.equal(prevented, true);
    assert.equal(lightbox.hidden, true);
});
