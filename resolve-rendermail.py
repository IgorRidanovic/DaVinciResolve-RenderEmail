#! /usr/bin/env python
# -*- coding: utf-8 -*-

# DaVinci Resolve render completion notification script.
# Copyright (c) 2020, Igor Ridanovic, Meta Fide
# This software is licensed under MIT licence.
# You can find the complete license file here: www.mylicencefile.com

# Where to place this script:
# MacOS:   /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp/
# Windows: %AppData%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Comp
# Linux:   /opt/resolve/Fusion/Scripts/Comp/

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import time
import sys

vers = '1.0.0'

class RenderMailer(object):
	def __init__(self):

		# ---- START USER CONFIGURATION ----

		# This is where you setup your email credentials for Gmail or other service.
		# The script will hang if the SMTP server information is incorrect!
		self.cfg = {'SMTP server':'smtp.gmail.com:587',
					'Username':'yourname@gmail.com',
					'Password':'EnterPasswordHere',
					'Sender': 'yourname@gmail.com'}

		# This is the list of recipients. To send an SMS you can use: '<YourNumber>@<SMS Gateway>'.
 		# For example, a T-Mobile subscriber (555) 555-0123 would be '5555550123@tmomail.net'.
		self.recipients = ['igor@hdhead.com']#, '5555550123@tmomail.net']

		# ---- END USER CONFIGURATION ----

	def msg(self,m):
		# STDOUT reporting
		print 'Render Mail:', m

	def api_refresh(self):
		# Are we running in the Resolve console?
		try:
			self.resolve     = bmd.scriptapp('Resolve')
			self.projManager = self.resolve.GetProjectManager()
			self.project	 = self.projManager.GetCurrentProject()
			return 'Created Resolve instances.'

		# We're not. Let's use the Blackmagic canonical import of the API library.
		except NameError:
			from python_get_resolve import GetResolve
			self.resolve = GetResolve()
# check what happens in an exception. this is the bmd method
			try:
				# API not found or Resolve Studio not running
				if False in self.resolve:
					return(self.resolve[1])
			except TypeError:
				# getresolve() didn't return False. It returned a Resolve object, hence the TypeError.
				# API is initiated. Create all pertinent Resolve instances.
				self.projManager = self.resolve.GetProjectManager()
				self.project	 = self.projManager.GetCurrentProject()
				return 'Created Resolve instances.'

	def render_complete(self):
		# Is any job currently rendering?
		if self.project.IsRenderingInProgress():

			# At least one job is rendering. Get all jobs.
			jobs = self.project.GetRenderJobs()

			# We'll track which job names were rendered
			self.completedjobs = {}

			# Infinitely loop through all individual jobs until 'Rendering' status is no longer present.
			for indx in jobs.keys():
				while 'Rendering' == self.project.GetRenderJobStatus(indx)['JobStatus']:
					# Local progress reporting.
					jobName         = jobs[indx]['RenderJobName']
					percentComplete = str(self.project.GetRenderJobStatus(indx)['CompletionPercentage'])
					self.msg('Rendering ' + jobName + ' ' + percentComplete + '%')

					# Slow down status checking. No need to overload the API.
					time.sleep(5)

					# Add the completed job name.
					self.completedjobs[jobName] = True

			self.msg('All renders are complete.')
			return True

		# No render jobs in progress
		return False

	def send_mail(self, subject, messageBody):
		self.msg('Sending email.')

		msg = MIMEMultipart('alternative')
		msg['From'] = self.cfg['Sender']
		msg['To'] = ','.join(self.recipients)
		msg['Subject'] = subject

		msg.attach(MIMEText(messageBody, 'plain'))
		# Optional HTML body.
		# msg.attach(MIMEText(htmlContent, 'html'))

		server = smtplib.SMTP(self.cfg['SMTP server'])
		server.starttls()
		try:
			server.login(self.cfg['Username'],self.cfg['Password'])
		except smtplib.SMTPAuthenticationError:
			self.msg('Exiting. Check your email username or password.')
			sys.exit(1)
		server.sendmail(self.cfg['Sender'], self.recipients,  msg.as_string())
		server.quit()

	def run(self):
		self.msg('Version ' + vers)
		self.msg('www.metafide.com\n')

		# Reload API each time we call run() just in case Resolve was restarted since we made the RenderMailer instance.
		self.msg(rm.api_refresh())

		# Delay to give user time to start render jobs after executing this script.
		time.sleep(10)

		# All renders are completed. Let's do something, i.e. send an email.
		if self.render_complete():

			# Compose the subject and the body of the email.
			subject = 'Render is complete.'
			completedjobslist = self.completedjobs.keys()
			completedjobs = ', '.join(completedjobslist)
			localTime     = time.asctime(time.localtime(time.time()))
			messageBody   = 'Resolve render finished at %s for the following jobs:\n%s.' %(localTime, completedjobs)

			# Send emails.
			self.send_mail(subject, messageBody)
			self.msg('Email sent.')

		else:
			self.msg('No renders in progress. Exiting.')


if __name__=='__main__':
	rm = RenderMailer()
	rm.run()
