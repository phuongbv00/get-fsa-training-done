"""Editing a vendor workbook without disturbing anything we did not write.

The FPT forms carry more than cells: a logo, a sensitivity label, print setup,
data validations, merged ranges, comments. Loading and re-saving one with a
spreadsheet library loses parts — measured on the real template, an openpyxl
round trip drops the classification label, both custom-property blobs and all
four printer-settings parts, and the pipeline this replaces emitted 17 of the
template's 35 parts.

So nothing is "loaded". The workbook is a zip; the sheets being populated have
their XML rewritten, and every other part is copied through unchanged. That
needs no dependency beyond `zipfile` and `xml.etree`, and it is strictly more
faithful than reconstructing the file.
"""
