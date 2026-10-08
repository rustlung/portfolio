document.querySelectorAll("[data-project-gallery]").forEach((gallery) => {
    const track = gallery.querySelector("[data-gallery-track]");
    const items = Array.from(gallery.querySelectorAll("[data-gallery-item]"));
    const previousButton = gallery.querySelector("[data-gallery-previous]");
    const nextButton = gallery.querySelector("[data-gallery-next]");
    const lightbox = gallery.querySelector("[data-gallery-lightbox]");
    const lightboxImage = gallery.querySelector("[data-lightbox-image]");
    const lightboxCaption = gallery.querySelector("[data-lightbox-caption]");
    const lightboxClose = gallery.querySelector("[data-lightbox-close]");
    const lightboxPrevious = gallery.querySelector("[data-lightbox-previous]");
    const lightboxNext = gallery.querySelector("[data-lightbox-next]");
    let currentIndex = 0;
    let previouslyFocused = null;
    const dragThreshold = 6;
    let activePointerId = null;
    let pointerStartX = 0;
    let scrollStartX = 0;
    let dragOccurred = false;

    const scrollStep = () => {
        const firstItem = track.querySelector(".project-gallery__item");
        const gap = Number.parseFloat(getComputedStyle(track).columnGap) || 0;
        return firstItem ? firstItem.getBoundingClientRect().width + gap : track.clientWidth;
    };

    const updateScrollButtons = () => {
        const maximumScroll = track.scrollWidth - track.clientWidth;
        previousButton.disabled = track.scrollLeft <= 1;
        nextButton.disabled = track.scrollLeft >= maximumScroll - 1;
    };

    previousButton.addEventListener("click", () => {
        track.scrollBy({ left: -scrollStep(), behavior: "smooth" });
    });

    nextButton.addEventListener("click", () => {
        track.scrollBy({ left: scrollStep(), behavior: "smooth" });
    });

    track.addEventListener("scroll", updateScrollButtons, { passive: true });
    window.addEventListener("resize", updateScrollButtons);

    track.addEventListener("pointerdown", (event) => {
        if (event.pointerType === "touch" || event.button !== 0) return;
        activePointerId = event.pointerId;
        pointerStartX = event.clientX;
        scrollStartX = track.scrollLeft;
        dragOccurred = false;
    });

    track.addEventListener("pointermove", (event) => {
        if (event.pointerId !== activePointerId) return;
        const distance = event.clientX - pointerStartX;
        if (!dragOccurred && Math.abs(distance) > dragThreshold) {
            // Capturing on pointerdown reroutes a normal button click to the
            // track in some browsers. Capture only after an actual drag.
            dragOccurred = true;
            track.setPointerCapture(event.pointerId);
            track.classList.add("project-gallery__track--dragging");
        }
        if (dragOccurred) {
            event.preventDefault();
            track.scrollLeft = scrollStartX - distance;
        }
    });

    const finishPointerDrag = (event) => {
        if (event.pointerId !== activePointerId) return;
        if (track.hasPointerCapture(event.pointerId)) {
            track.releasePointerCapture(event.pointerId);
        }
        track.classList.remove("project-gallery__track--dragging");
        activePointerId = null;
    };

    track.addEventListener("pointerup", finishPointerDrag);
    track.addEventListener("pointercancel", finishPointerDrag);

    const showLightboxItem = (index) => {
        currentIndex = (index + items.length) % items.length;
        const thumbnailImage = items[currentIndex].querySelector("img");
        const caption = items[currentIndex].closest("figure").querySelector("figcaption");
        lightboxImage.src = thumbnailImage.src;
        lightboxImage.alt = thumbnailImage.alt;
        lightboxCaption.textContent = caption ? caption.textContent : "";
        lightboxCaption.hidden = !caption;
    };

    const openLightbox = (index) => {
        previouslyFocused = document.activeElement;
        showLightboxItem(index);
        lightbox.hidden = false;
        document.body.classList.add("lightbox-open");
        lightboxClose.focus();
    };

    const closeLightbox = () => {
        lightbox.hidden = true;
        lightboxImage.src = "";
        document.body.classList.remove("lightbox-open");
        if (previouslyFocused) previouslyFocused.focus();
    };

    items.forEach((item, index) => {
        item.addEventListener("click", (event) => {
            if (dragOccurred) {
                event.preventDefault();
                dragOccurred = false;
                return;
            }
            openLightbox(index);
        });
    });

    lightboxClose.addEventListener("click", closeLightbox);
    lightboxPrevious.addEventListener("click", () => showLightboxItem(currentIndex - 1));
    lightboxNext.addEventListener("click", () => showLightboxItem(currentIndex + 1));
    lightbox.addEventListener("click", (event) => {
        if (!event.target.closest(".project-lightbox__image") && !event.target.closest("button")) {
            closeLightbox();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (lightbox.hidden) return;
        if (event.key === "Escape") closeLightbox();
        if (event.key === "ArrowLeft") showLightboxItem(currentIndex - 1);
        if (event.key === "ArrowRight") showLightboxItem(currentIndex + 1);
    });

    const hasMultipleItems = items.length > 1;
    lightboxPrevious.hidden = !hasMultipleItems;
    lightboxNext.hidden = !hasMultipleItems;
    updateScrollButtons();
});
