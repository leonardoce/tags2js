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

The benefits of the XML description of the GUI components is more evident in
complex forms.

Examples
--------

You can find the examples in the "examples" subdirectory of this repository.

License
-------

This code is unlicensed. See http://unlicense.org.

