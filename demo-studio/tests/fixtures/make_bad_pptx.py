"""Build a minimal .pptx containing the constructs Google Slides drops, so the
guardrail has something real to catch."""
import sys
import zipfile

SLIDE_WITH_CONNECTOR = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:cxnSp><p:nvCxnSpPr/><p:spPr><a:prstGeom prst="straightConnector1"/></p:spPr></p:cxnSp>
    <p:sp><p:spPr><a:ln><a:prstDash val="dash"/></a:ln></p:spPr></p:sp>
  </p:spTree></p:cSld>
</p:sld>
"""

CLEAN_SLIDE = """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld><p:spTree>
    <p:sp><p:spPr><a:prstGeom prst="rightArrow"/><a:ln><a:solidFill/></a:ln></p:spPr></p:sp>
  </p:spTree></p:cSld>
</p:sld>
"""


def write(path, xml):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ppt/slides/slide1.xml", xml)


if __name__ == "__main__":
    kind, path = sys.argv[1], sys.argv[2]
    write(path, SLIDE_WITH_CONNECTOR if kind == "bad" else CLEAN_SLIDE)
