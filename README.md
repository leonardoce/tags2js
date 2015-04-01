tag2js
======

Tag2js is a simple Python tool to be used with Qooxdoo that reads XML
description files of GUI components and generates the corresponding Javascript
code to create the component. This means that you can write this:

```xml
<NavigationPage title="Login">
	<Script>
	<![CDATA[
	_initialize: function() {
		this._createComponents();
	},

	onButtonTap: function() {
		if (this.__form.validate()) {
			qx.core.Init.getApplication().getRouting().executeGet("/overview");
		}
	}
	]]>
	</Script>

	<Form enclosedIn="new qx.ui.mobile.form.renderer.Single" id="__form">
		<TextField id="user" required="json:true" layoutParams="'Username'"/>
		<PasswordField id="pwd" required="json:true" layoutParams="'Password'"/>
	</Form>
	<Button label="Login" onTap="onButtonTap"/>
</NavigationPage>
```

instead of:

```javascript
qx.Class.define("mobileHello.page.Login",
{
  extend : qx.ui.mobile.page.NavigationPage,

  construct : function()
  {
    this.base(arguments);
    this.setTitle("Login");
  },


  members :
  {
    __form: null,

    _initialize: function() {
      this.base(arguments);

      // Username
      var user = new qx.ui.mobile.form.TextField();
      user.setRequired(true);

      // Password
      var pwd = new qx.ui.mobile.form.PasswordField();
      pwd.setRequired(true);

      // Login Button
      var loginButton = new qx.ui.mobile.form.Button("Login");
      loginButton.addListener("tap", this._onButtonTap, this);

      var loginForm = this.__form = new qx.ui.mobile.form.Form();
      loginForm.add(user, "Username");
      loginForm.add(pwd, "Password");

      // Use form renderer
      this.getContent().add(new qx.ui.mobile.form.renderer.Single(loginForm));
      this.getContent().add(loginButton);
    },

    _onButtonTap: function() {
      // use form validation
      if (this.__form.validate()) {
        qx.core.Init.getApplication().getRouting().executeGet("/overview");
      }
    }
  }
});
```

The benefits of the XML description of the GUI components are more evident in
complex forms.

Examples
--------

You can find the examples in the "examples" subdirectory of this repository.

Usage
-----

You need to copy the `tojs.py` file in your project directory and then you must
create the `tojs_config.json` file following this example:

```javascript
{
    "aliases": {
        "Button": "qx.ui.mobile.form.Button",
        "Composite": "qx.ui.mobile.container.Composite",
        "Form": "qx.ui.mobile.form.Form",
        "Label": "qx.ui.mobile.basic.Label",
        "NavigationPage": "qx.ui.mobile.page.NavigationPage",
        "TextField": "qx.ui.mobile.form.TextField",
        "PasswordField": "qx.ui.mobile.form.PasswordField"
    },
    
    "defaultPackage" : "qx.ui.mobile"
}
```

The `aliases` attribute specifies the mapping between tag names and the
relative Qooxdoo constructor class. When `tojs.py` doesnt's spot a mapping it
tries to find the component inside the `defaultPackage`.

Tags2js will write the code that created your components inside the
`_createComponents` method, that you can call when you think that is useful.

In the XML files the root element represent the root object and `tojs` will
generate a class that inherits from the one you specified as root element.
Attributes are components properties.

There are some special entities and some special attributes.

Special entities
----------------

Special entities can be put only in the root element.

The `Script` entity contains Javascript code to be included inside the
generated javascript file.

The `Constructor`, `Destructor` contains code to be included in the generated
constructor or descructor.

License
-------

This code is unlicensed. See http://unlicense.org.

