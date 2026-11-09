# Using Course Tree

Course Tree shows a course as one big tree: the course at the top, one branch per week,
and the concepts of each week below it. Every node has a definition you can read, edit and
study as a flashcard. To install it, see [SETUP.md](SETUP.md).

Start the app with `python -m app.main` and open **http://127.0.0.1:8050**.

## The screen

- **Left:** the tree. Above it is the toolbar: tree picker, **+ New tree**, **📚 Study**,
  **📄 PDF**, **↶ Undo**, **↷ Redo**, **Fit to screen**, **Collapse all**, **Expand all**
  and the search box.
- **Right:** the side panel, showing the selected node's path, title and definition, and
  its buttons.
- **The grey bar between them:** drag it to make the panel wider (more room to write) or
  narrower (more room for the tree). Double-click it to go back to the default width. The
  width is remembered.

## Moving around the tree

| Do this | To |
|---|---|
| Scroll the mouse wheel | zoom in and out wherever the pointer is |
| Drag the empty background | move around |
| Click a node | select it and read its definition in the side panel |
| **Fit to screen** | see the whole tree again |
| Type in **Search nodes…** and pick a result | jump to that node: its branch opens, it is selected and the view zooms to it |
| **Collapse** in the panel | hide everything below the selected node (it then shows `▸ N`, the number of hidden nodes) |
| **Expand** in the panel | show it again |
| **Collapse all** / **Expand all** | fold the tree down to the weeks, or open everything |

## Adding and editing nodes

**Add a node:** select its parent, then click the yellow **+** that appears below it in the
tree (or **+ Add child** in the panel). Type a **Label** (the short name shown in the
tree) and a **Definition**, then **Save**.

**Edit a node:** select it and press **Edit**. **Delete** removes the node and everything
below it, after asking you to confirm. The top node of a tree cannot be deleted.

While you edit, the editor stays still and only the **Preview** box below it scrolls.
After you type, the preview jumps to the part you are writing, so text added at the end
appears at the bottom. Drag the bottom-right corner of the definition box to make it
taller or shorter.

### Writing definitions

Definitions use **Markdown**:

| Write | Shows |
|---|---|
| `**bold**`, `*italic*` | **bold**, *italic* |
| `- item` on separate lines | a bullet list |
| `1. item` | a numbered list |
| a blank line | a new paragraph |
| a header row such as `\| A \| B \|`, then `\|---\|---\|`, then rows | a table |
| `$\frac{TP}{TP+FN}$` | an inline formula (LaTeX) |
| `$$\text{PPV} = \frac{TP}{TP+FP}$$` | a formula on its own line |

### Pictures

While editing a definition:

- **Paste** a screenshot or copied picture straight into the definition box (Ctrl+V), or
- **drop** an image file on the "🖼 Add an image" area, or click the area to choose one.

PNG, JPEG, GIF and WebP up to 10 MB are accepted. The picture is saved in `data/images/` and
a line like `![caption](/images/....png)` is added to the definition; you can move that line
anywhere in the text. Click a picture in a definition to open it full size.

## Week colours

Every week has its own colour, and the nodes inside it are lighter shades of it. To choose
a week's colour, click the week node: the panel shows **Week colour**.

- Click one of the 16 swatches, or
- type any colour such as `#e76f51` in the box and press **Use**, or
- press **Automatic** to go back to the default colour.

Text automatically turns dark on light colours so it stays readable.

## Undo and redo

**↶ Undo** / **↷ Redo** in the toolbar, or **Ctrl+Z** / **Ctrl+Y** (also Ctrl+Shift+Z),
undo and redo adding, editing, deleting, flashcard switches and colour changes, including a
whole deleted branch. Hover the buttons to see what they will undo or redo. The last 200
changes of each tree are kept, even after you restart the app. While you are typing in a
text box, Ctrl+Z undoes your typing instead.

## Study mode (flashcards)

Press **📚 Study**. It opens in a new browser tab or window, so you can keep the tree open
next to it.

1. Choose the tree and the **week**.
2. A random concept from that week appears as a card showing only its name.
3. Click the card (or press **Space**) to see the definition.
4. Mark yourself honestly: **✓ I knew it** (→ or **Y**) or **✗ I didn't know it** (← or
   **N**). The next random card appears.
5. At the end you see your score (for example `4 / 6 correct, 67%`), the list of concepts
   you missed, **Retry the N I missed**, and **Start again**.

**Include sub-concepts** tests you on every level inside the week, not just the concepts
directly under it. **Shuffle & restart** deals a new random order.

### Choosing which nodes are flashcards

Select a node and press **🃏 Flashcard: on** in the panel to switch it to **🚫 Flashcard:
off**. That node is then skipped in study mode, and appears faded with a dotted outline in
the tree. Press it again to include it. Only that node changes; nodes below it can still be
cards. The top node and the weeks are never cards, so their button is greyed out.

## PDF windows

Press **📄 PDF** (or drag a PDF file from your computer onto the page) to open it in a small
floating window over the tree, so you can read your slides while you take notes.

- Drag the window by its dark title bar.
- Resize it from any edge or corner.
- `□` maximises it to fill the browser window (or double-click the title bar); press again
  to restore.
- `–` shrinks it to just the title bar; `↗` opens it in a full browser tab; `×` closes it.

You can open several PDFs at once. The files are not uploaded or saved anywhere, so after
reloading the page you open them again.

## Several trees (one per course)

The dropdown at the top left switches between trees. **+ New tree** starts a completely
separate one: type a name (it becomes the top node), press **Create**. Each tree has its
own database and its own `.json` file in `data/trees/`, and its own undo history. The app
remembers which tree you were looking at. Study mode lets you pick the tree too.

## Saving and backing up

Everything you do is saved immediately in the tree's database (`data/trees/<name>.db`);
there is no Save-all button to remember. To make a backup, or to move your notes to another
computer, export the trees to their `.json` files and commit them:

```bash
python -m app.export_json
git add data/trees data/images
git commit -m "Update course notes"
git push
```

See [SETUP.md](SETUP.md#6-moving-your-notes-between-computers) for loading them on another
computer.

## Keyboard shortcuts

| Where | Keys | Action |
|---|---|---|
| Tree page | Ctrl+Z | undo |
| Tree page | Ctrl+Y or Ctrl+Shift+Z | redo |
| Definition box | Ctrl+V with a picture copied | add the picture |
| Study page | Space or Enter | flip the card |
| Study page | → or Y | I knew it |
| Study page | ← or N | I didn't know it |
