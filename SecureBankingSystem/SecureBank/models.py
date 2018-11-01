# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import User
from django.db.models import CASCADE, SET_NULL
from pyotp import random_base32, TOTP, totp
from .utils import SecureBankException
from django.contrib.auth.models import AbstractUser
from django.db import transaction
# from Crypto.PublicKey import RSA
# from Crypto import Random



class BankUser(models.Model):
    MAX_REGULAR_EMPLOYEE = 100000
    MAX_AUTO_AUTH = 10000
    BITS = 1024
    # class Meta:
    #     permissions = (
    #         ("is_External_User", "Customer of bank"),
    #         ("is_Internal_User", "Employee has permissions to access User data"),
    #         ("is_Manager", "Manager has permission to access transactions")
    #     )

    TYPES = (
        ('R', 'Regular Employee'),
        ('S', 'System Manager'),
        ('A', 'Admin'),
        ('I', "Individual Customer"),
        ('O', 'Organization'),
    )
    # UID ( Primary Key ), Last Login, Last transaction, last password change, failed login attempt, type of user
    user = models.OneToOneField(User, unique=True, on_delete=CASCADE, primary_key=True)
    phone = models.CharField(max_length=10)
    EmailID = models.EmailField(max_length=70, null=False)
    address = models.CharField(max_length=250)
    otp_value = models.CharField(max_length=16, default='0', editable=False)
    type_of_user = models.CharField(max_length=1, choices=TYPES)

    # private_key = models.CharField()
    # public_key = models.CharField()
    # ListCharField (Internal User, Account access for Internal user). https://django-mysql.readthedocs.io/en/latest/model_fields/list_fields.html

    # TODO: Need to add OTP creation time (for validity of OTP)

    def __str__(self):
        return self.user.username + " " + self.type_of_user

    def generateCerti(self):
        newKey = RSA.generate(BITS)
        self.public_key = newKey.publickey().exportKey("PEM")
        self.private_key = newKey.exportKey("PEM")
        # sendMail(self.public_key)

    # https://pyotp.readthedocs.io/en/latest/
    def generateOTP(self):
        self.otp_value = TOTP('base32secret3232', interval=120).now()
        self.save()
        subject = 'OTP From Secure Bank'
        message = self.otp_value
        from_email = 'systemadmin007@gmail.com'
        print(self.EmailID)
        to = [self.EmailID]
        print(self.otp_value)
        send_mail(subject, message, from_email, to, fail_silently=False)
        return self.otp_value
        # djexmo.send_message(frm='+919717384229', to='+918700543963', text='My sms')
        # zerosms.sms(phno=username, passwd=password, receivernum=sendto, message=msg)

    def verifyOTP(self, otp):
        pot = TOTP('base32secret3232', interval=120)
        value = pot.verify(otp)
        print('value', value)
        return pot.verify(otp)


# class Payment(models.Model):
#     # TODO: Need to create Payment SQLite Table here
#     organization = models.ForeignKey(BankUser, related_name="merchant", null=True)
#     user = models.ForeignKey(Account, related_name='user', null=True)
#     transaction = models.ForeignKey(Transaction, related_name='transaction')
#

class Account(models.Model):
    AccountNumber = models.IntegerField(primary_key=True, unique=True)
    AccountHolder = models.ForeignKey(BankUser, null=True, on_delete=True)
    Balance = models.IntegerField(default=0, editable=True)

    def __str__(self):
        return str(self.AccountNumber)
        # return self.AccountHolder.user.username + " " + str(self.AccountNumber) + " " + str(self.Balance)

    def Credit(self, amount):
        try:
            self.Balance = self.Balance + int(amount)
            self.save()
        except:
            raise SecureBankException('Invalid Amount')

    def Debit(self, amount):
        try:
            if (amount <= 0):
                raise SecureBankException("Invalid Amount")
            if self.Balance < amount:
                raise SecureBankException("Insufficient Funds")
            self.Balance = self.Balance - int(amount)
            self.save()
        except:
            raise SecureBankException('Not Debited!')


class Transaction(models.Model):
    STATUS = (
        ('O', 'OTP required'),
        ('A', 'Approval required'),
        ('P', 'Processed'),
        ('R', 'Rejected'),
        ('E', 'Unsuccessful'),
    )

    TYPE = (
        ('C', 'Credit'),
        ('D', 'Debit'),
        ('T', 'Transfer'),
    )
    Employee = models.ForeignKey(BankUser, null=True, blank=True, on_delete=SET_NULL)
    FromAccount = models.ForeignKey(Account, null=True, related_name='FromAccount', on_delete=SET_NULL, blank=True)
    ToAccount = models.ForeignKey(Account, null=True, related_name='ToAccount', on_delete=SET_NULL, blank=True)
    Amount = models.IntegerField(default=0, editable=False)
    Status = models.CharField(max_length=1, choices=STATUS, editable=False)
    Type = models.CharField(max_length=1,default='T',choices=TYPE,editable=False)
    CreationTime = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        if self.Type == 'T':
            return str(self.id) + " " + str(self.FromAccount.AccountNumber) + " " + str(
                self.ToAccount.AccountNumber) + " " + str(self.Amount)
        elif self.Type == 'D':
            return str(self.id) + " " + str(self.FromAccount.AccountNumber) + " " + str(self.Amount)
        else:
            return str(self.id) + " " + str(self.ToAccount.AccountNumber) + " " + str(self.Amount)

    @staticmethod
    def Create(user, fromAccountNumber, toAccountNumber, amount):
        try:
            amount = int(amount.strip())
        except:
            raise SecureBankException('Error in account number')
        if (amount <= 0):
            raise SecureBankException('Negative Ammount')
        fromAccount = Account.objects.filter(AccountNumber=fromAccountNumber)
        if len(fromAccount) == 0:
            raise SecureBankException("Account belongs to someone else")
        fromAccount = fromAccount[0]
        if fromAccount.AccountHolder.user.username != user.username:
            raise SecureBankException("Trying to access someones else account")
        if fromAccount.Balance < amount:
            raise SecureBankException("Insufficient Funds")
        toAccount = Account.objects.filter(AccountNumber=toAccountNumber)
        if len(toAccount) == 0:
            raise SecureBankException('Cannot send to this account')
        toAccount = toAccount[0]
        if fromAccount.AccountNumber == toAccount.AccountNumber:
            raise SecureBankException("Cannot transfer to same account")
        transaction = Transaction(FromAccount=fromAccount, ToAccount=toAccount, Amount=amount, Status='O', Type='T')
        print("Done")
        transaction.save()
        return transaction

    @staticmethod
    def CreateCredit(user, fromAccountNumber, amount):
        print("Do Credit Here")
        try:
            amount = int(amount.strip())
        except:
            raise SecureBankException('Error in account number')
        if (amount <= 0):
            raise SecureBankException('Negative Ammount')
        fromAccount = Account.objects.filter(AccountNumber=fromAccountNumber)
        if len(fromAccount) == 0:
            raise SecureBankException("Account belongs to someone else")
        fromAccount = fromAccount[0]
        if fromAccount.AccountHolder.user.username != user.username:
            raise SecureBankException("Trying to access someones else account")
        transaction = Transaction(FromAccount=None, ToAccount=fromAccount, Amount=amount, Status='P', Type='C')
        fromAccount.Credit(amount)
        transaction.save()

    @staticmethod
    def CreateDebit(user, fromAccountNumber, amount):
        print("Do Debit Here")
        try:
            amount = int(amount.strip())
        except:
            raise SecureBankException('Error in account number')
        if (amount <= 0):
            raise SecureBankException('Negative Ammount')
        fromAccount = Account.objects.filter(AccountNumber=fromAccountNumber)
        if len(fromAccount) == 0:
            raise SecureBankException("Account belongs to someone else")
        fromAccount = fromAccount[0]
        if fromAccount.AccountHolder.user.username != user.username:
            raise SecureBankException("Trying to access someones else account")
        if fromAccount.Balance < amount:
            raise SecureBankException("Insufficient Funds")
        if amount > BankUser.MAX_AUTO_AUTH:
            transaction = Transaction(FromAccount=fromAccount, ToAccount=None, Amount=amount, Status='A', Type='D')
        else:
            transaction = Transaction(FromAccount=fromAccount, ToAccount=None, Amount=amount, Status='P', Type='D')
            fromAccount.Debit(amount)
        transaction.save()
        return transaction

    def verify_otp(self, otpvalue):
        try:
            otp = int(otpvalue)
        except:
            self.Status = 'E'
            self.save
            raise SecureBankException('Invalid OTP Here')

        if not self.FromAccount.AccountHolder.verifyOTP(otp):
            self.Status = 'E'
            self.save
            raise SecureBankException('Invalid OTP')

        if( self.Amount > BankUser.MAX_AUTO_AUTH):
            self.Status = 'A'
        else:
            self.Status = 'P'
        print(self.Status)
        self.save()

    @transaction.atomic
    def approve_transaction(self):
        print("Approve")
        if (self.ToAccount == None):
            self.FromAccount.Debit(self.Amount)
        else:
            self.FromAccount.Debit(self.Amount)
            self.ToAccount.Debit(self.Amount)
        self.Status = "P"
        self.save()
        return self.Status

    def reject_transaction(self):
        print("Reject Transaction")
        self.Status = 'R'
        self.save()
        return self.Status

    def mark_error(self):
        print("Error transaction")
        self.Status = 'E'
        self.save()
        return self.Status


class LoggedInUser(models.Model):
    user = models.OneToOneField(User, related_name='logged_in_user', on_delete=SET_NULL, null=True)
    session_key = models.CharField(max_length=32, null=True, blank=True)
    name = models.CharField(max_length=70, null=True, blank=True)

    def __str__(self):
        return self.user.username
