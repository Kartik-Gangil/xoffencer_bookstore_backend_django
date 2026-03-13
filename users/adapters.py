from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        This is the method that was causing the error.
        We override it to correctly save the user from the API data.
        """
        # The cleaned_data is safe data from the form
        data = form.cleaned_data
        
        user.username = data.get('username')
        user.email = data.get('email')
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.is_active = True # Ensure the user can log in

        # --- THE KEY FIX ---
        # The password is not in cleaned_data. We get it from the raw form data.
        # We use 'password' here because our frontend sends 'password1' but the
        # default serializer renames it to 'password' internally.
        password = form.initial_data.get('password')
        if not password:
            # Fallback for the field name
            password = form.initial_data.get('password1')
        
        user.set_password(password)

        if commit:
            user.save()
        
        return user
