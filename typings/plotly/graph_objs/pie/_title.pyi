"""
This type stub file was generated by pyright.
"""

from plotly.basedatatypes import BaseTraceHierarchyType as _BaseTraceHierarchyType

class Title(_BaseTraceHierarchyType):
    _parent_path_str = ...
    _path_str = ...
    _valid_props = ...
    @property
    def font(self): # -> tuple[Any, ...] | Self | None:
        """
        Sets the font used for `title`. Note that the title's font used
        to be set by the now deprecated `titlefont` attribute.

        The 'font' property is an instance of Font
        that may be specified as:
          - An instance of :class:`plotly.graph_objs.pie.title.Font`
          - A dict of string/value properties that will be passed
            to the Font constructor

            Supported dict properties:

                color

                colorsrc
                    Sets the source reference on Chart Studio Cloud
                    for `color`.
                family
                    HTML font family - the typeface that will be
                    applied by the web browser. The web browser
                    will only be able to apply a font if it is
                    available on the system which it operates.
                    Provide multiple font families, separated by
                    commas, to indicate the preference in which to
                    apply fonts if they aren't available on the
                    system. The Chart Studio Cloud (at
                    https://chart-studio.plotly.com or on-premise)
                    generates images on a server, where only a
                    select number of fonts are installed and
                    supported. These include "Arial", "Balto",
                    "Courier New", "Droid Sans",, "Droid Serif",
                    "Droid Sans Mono", "Gravitas One", "Old
                    Standard TT", "Open Sans", "Overpass", "PT Sans
                    Narrow", "Raleway", "Times New Roman".
                familysrc
                    Sets the source reference on Chart Studio Cloud
                    for `family`.
                size

                sizesrc
                    Sets the source reference on Chart Studio Cloud
                    for `size`.
                style
                    Sets whether a font should be styled with a
                    normal or italic face from its family.
                stylesrc
                    Sets the source reference on Chart Studio Cloud
                    for `style`.
                variant
                    Sets the variant of the font.
                variantsrc
                    Sets the source reference on Chart Studio Cloud
                    for `variant`.
                weight
                    Sets the weight (or boldness) of the font.
                weightsrc
                    Sets the source reference on Chart Studio Cloud
                    for `weight`.

        Returns
        -------
        plotly.graph_objs.pie.title.Font
        """
        ...
    
    @font.setter
    def font(self, val): # -> None:
        ...
    
    @property
    def position(self): # -> tuple[Any, ...] | Self | None:
        """
        Specifies the location of the `title`. Note that the title's
        position used to be set by the now deprecated `titleposition`
        attribute.

        The 'position' property is an enumeration that may be specified as:
          - One of the following enumeration values:
                ['top left', 'top center', 'top right', 'middle center',
                'bottom left', 'bottom center', 'bottom right']

        Returns
        -------
        Any
        """
        ...
    
    @position.setter
    def position(self, val): # -> None:
        ...
    
    @property
    def text(self): # -> tuple[Any, ...] | Self | None:
        """
        Sets the title of the chart. If it is empty, no title is
        displayed. Note that before the existence of `title.text`, the
        title's contents used to be defined as the `title` attribute
        itself. This behavior has been deprecated.

        The 'text' property is a string and must be specified as:
          - A string
          - A number that will be converted to a string

        Returns
        -------
        str
        """
        ...
    
    @text.setter
    def text(self, val): # -> None:
        ...
    
    def __init__(self, arg=..., font=..., position=..., text=..., **kwargs) -> None:
        """
        Construct a new Title object

        Parameters
        ----------
        arg
            dict of properties compatible with this constructor or
            an instance of :class:`plotly.graph_objs.pie.Title`
        font
            Sets the font used for `title`. Note that the title's
            font used to be set by the now deprecated `titlefont`
            attribute.
        position
            Specifies the location of the `title`. Note that the
            title's position used to be set by the now deprecated
            `titleposition` attribute.
        text
            Sets the title of the chart. If it is empty, no title
            is displayed. Note that before the existence of
            `title.text`, the title's contents used to be defined
            as the `title` attribute itself. This behavior has been
            deprecated.

        Returns
        -------
        Title
        """
        ...
    


