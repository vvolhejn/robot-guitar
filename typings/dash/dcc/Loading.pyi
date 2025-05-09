"""
This type stub file was generated by pyright.
"""

from dash.development.base_component import Component, _explicitize_args

class Loading(Component):
    """A Loading component.
    A Loading component that wraps any other component and displays a spinner until the wrapped component has rendered.

    Keyword arguments:

    - children (list of a list of or a singular dash component, string or numbers | a list of or a singular dash component, string or number; optional):
        Array that holds components to render.

    - id (string; optional):
        The ID of this component, used to identify dash components in
        callbacks. The ID needs to be unique across all of the components
        in an app.

    - className (string; optional):
        Additional CSS class for the built-in spinner root DOM node.

    - color (string; default '#119DFF'):
        Primary color used for the built-in loading spinners.

    - custom_spinner (a list of or a singular dash component, string or number; optional):
        Component to use rather than the built-in spinner specified in the
        `type` prop.

    - debug (boolean; optional):
        If True, the built-in spinner will display the component_name and
        prop_name while loading.

    - delay_hide (number; default 0):
        Add a time delay (in ms) to the spinner being removed to prevent
        flickering.

    - delay_show (number; default 0):
        Add a time delay (in ms) to the spinner being shown after the
        loading_state is set to True.

    - display (a value equal to: 'auto', 'show', 'hide'; default 'auto'):
        Setting display to  \"show\" or \"hide\"  will override the
        loading state coming from dash-renderer.

    - fullscreen (boolean; optional):
        Boolean that makes the built-in spinner display full-screen.

    - loading_state (dict; optional):
        Object that holds the loading state object coming from
        dash-renderer.

        `loading_state` is a dict with keys:

        - component_name (string; optional):
            Holds the name of the component that is loading.

        - is_loading (boolean; optional):
            Determines if the component is loading or not.

        - prop_name (string; optional):
            Holds which property is loading.

    - overlay_style (dict; optional):
        Additional CSS styling for the spinner overlay. This is applied to
        the dcc.Loading children while the spinner is active.  The default
        is `{'visibility': 'hidden'}`.

    - parent_className (string; optional):
        Additional CSS class for the outermost dcc.Loading parent div DOM
        node.

    - parent_style (dict; optional):
        Additional CSS styling for the outermost dcc.Loading parent div
        DOM node.

    - show_initially (boolean; default True):
        Whether the Spinner should show on app start-up before the loading
        state has been determined. Default True.  Use when also setting
        `delay_show`.

    - style (dict; optional):
        Additional CSS styling for the built-in spinner root DOM node.

    - target_components (dict with strings as keys and values of type string | list of strings; optional):
        Specify component and prop to trigger showing the loading spinner
        example: `{\"output-container\": \"children\", \"grid\":
        [\"rowData\", \"columnDefs]}`.

    - type (a value equal to: 'graph', 'cube', 'circle', 'dot', 'default'; default 'default'):
        Property that determines which built-in spinner to show one of
        'graph', 'cube', 'circle', 'dot', or 'default'."""
    _children_props = ...
    _base_nodes = ...
    _namespace = ...
    _type = ...
    @_explicitize_args
    def __init__(self, children=..., id=..., type=..., fullscreen=..., debug=..., className=..., parent_className=..., style=..., parent_style=..., overlay_style=..., color=..., loading_state=..., display=..., delay_hide=..., delay_show=..., show_initially=..., target_components=..., custom_spinner=..., **kwargs) -> None:
        ...
    


