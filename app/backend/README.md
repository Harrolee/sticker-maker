## Field Notes

the default model in remove() seems to change the color profile of input images to be cooler

### creating a tab

- must do immediately after creating a border
  - the border-find algorithm relies on there not being any gradient to the border
- must apply border post-processing effects AFTER making the tab

  - round the border's edges
  - create a gradient for the border

- must do after cartoonizing input image

- consider cartoonizing the border and then compositing it over the image
