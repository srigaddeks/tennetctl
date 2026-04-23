# 01_post_composer — Design

The Composer uses a split-pane architecture: a unified input on the left and a network-specific preview carousel on the right.

## UI Components
- **Channel Selector**: A horizontal strip of connected profile icons (Avatar + Network Icon).
- **Drafting Area**:
    - **Global Text**: Shared content for all selected channels.
    - **Channel Overrides**: Toggleable text areas for network-specific captions.
- **Media Tray**:
    - Supports `PNG, JPG, MP4`.
    - Integrated button for **Canva** (opens in iframe/modal).
    - **Alt-Text** drawer for accessibility.
- **Preview Pane**: A dynamic simulator that mimics the CSS of the target platforms (Mobile/Desktop views).

## Data Model (Implied)
- **Draft Entity**:
    - `id`: UUID
    - `global_text`: Text
    - `media_attachments`: List of Media IDs
    - `channel_settings`: JSONB (e.g., `{ "linkedin": { "text": "...", "comment": "..." } }`)
- **State Management**:
    - Active networks: `List<ProfileID>`
    - Validation State: `Map<ProfileID, Boolean>` (e.g., character limit check).

## AI Workflow
- **Input**: User selects a text block.
- **Action**: Call to `/api/v1/ai/generate` with current context and selected prompt (Summarize, Rewrite).
- **Response**: Returns 3 variants; user chooses one to replace or append to the editor.
