# Import dependices.
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from time import sleep
import numpy as np
import pymsteams
import os
import click
import sys
from datetime import datetime

@click.command()
@click.option('--email', prompt='Email', help="MS Office 365 Email")
@click.option('--password', prompt='Password', help="MS Office 365 Password")
@click.option('--year', prompt='Year', help="Year Group")
@click.option('--schoolwise', prompt='SchoolWise', help="SchoolWise URL for Class")
@click.option('--subject', prompt='Subject', help="Subject Name")
@click.option('--teacher', prompt='Teacher', help="Teacher of Class")
@click.option('--teams', prompt='Teams Channel', help="URL for Teams channel")
def script(email, password, year, schoolwise, subject, teacher, teams):
    while True:
        try:
            # Web Driver.
            driver = webdriver.Safari()

            # Class Group SchoolWise URL.
            url = schoolwise

            # Retrieve page.
            driver.get(url)

            # LogIn Screen.
            # Find login button.
            # ID name.
            id_of_login_button = "dnn_ctr1481_Login_Login_Azure_loginButton"

            # Find button.
            login_button = driver.find_element_by_id(id_of_login_button)

            # Click login button.
            driver.execute_script("arguments[0].click();", login_button)

            # Microsoft Office 365 LogIn.
            EMAILFIELD = (By.ID, "i0116")
            PASSWORDFIELD = (By.ID, "i0118")
            NEXTBUTTON = (By.ID, "idSIButton9")
            NOBUTTON = (By.ID, "idBtn_Back")

            # Wait for email field and enter email.
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(EMAILFIELD)).send_keys(email)

            # Click Next.
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(NEXTBUTTON)).click()

            # Wait.
            sleep(1)

            # Wait for password field and enter password.
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(PASSWORDFIELD)).send_keys(password)

            # Click Login.
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(NEXTBUTTON)).click()

            # Reduce number of logins - yes.
            sleep(5)
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(NEXTBUTTON)).click()
            sleep(15)

            # LogIn was successful, proceed to gather assignments by Mr O'Sullivan.
            # Find assignments.
            assignment = driver.find_elements_by_class_name("action-container")[0]

            # Iterate through assignments.
            posts_content = []
            links = []
                
            # Find and click view assignments button.
            view_button = assignment.find_element_by_css_selector("button")
            driver.execute_script("arguments[0].click();", view_button)

            # Get title of assignment
            title = driver.find_element_by_xpath("//p[@ng-bind-html='vm.Assessment.Title']").text

            # Get instructions.
            instructions = driver.find_element_by_xpath("//p[@ng-bind-html='vm.Assessment.Instructions | AsHtml']").text

            # Get due date.
            right_container = driver.find_elements_by_class_name("right-container")[2]
            due_date = right_container.find_element_by_css_selector("p").text
            due_date_datetime = datetime.strptime(due_date, '%d %b %Y %H:%M')

            # Get file.
            try:
                # Find element.
                link_elem = driver.find_element_by_class_name('file-properties')

                # Click link.
                driver.execute_script("arguments[0].click();", link_elem)

                # Switch to new tab.
                sleep(10)
                driver.switch_to.window(driver.window_handles[-1])
                sleep(5)

                # Get link.
                link = driver.current_url
                links.append(link)

                # Close tab.
                driver.close()

                # Switch to original tab.
                driver.switch_to.window(driver.window_handles[0])
            except:
                link = "no_link"
                links.append(link)

            if datetime.now() < due_date_datetime:
                # Combine information to output.
                # Start and end of post output.
                intro = "SchoolWise API | \n\n"
                output = intro
                metadata = "Author: {}".format(teacher) + ", Due Date: " + due_date

                # Title.
                output += "Title: \n" + title + "\n\n"

                # Instructions.
                output += "Instructions: \n" + instructions + "\n\n"
                
                # Add metadata.
                output += metadata

                # Add to list.
                posts_content.append(output)

                # Wait.
                sleep(5)

                # Define link to Teams channel.
                teams_channel = teams

                # Have the latest posts at start of list.
                posts_content = posts_content[::-1]
                links = links[::-1]

                # Add check to see if post has already been made.
                try:
                    posts = np.load('{}/{}/assignment.npy'.format(year, subject))
                    old_posts, old_links = posts[0].tolist(), posts[1].tolist()
                    new_posts = [x for x in posts_content if x not in old_posts]
                    new_links = links[-len(new_posts):]
                except:
                    new_posts, new_links = posts_content, links

                # Post new messages to Teams.
                if len(new_posts) > 0 and len(new_links) == len(new_posts):
                    for i in range(len(new_posts)):
                        # Connect to channel.
                        myTeamsMessage = pymsteams.connectorcard(teams_channel)

                        # Compose message.
                        myTeamsMessage.text(new_posts[i])

                        # Add title.
                        myTeamsMessage.title("Assignment")

                        # Add link to files.
                        if not "no_link" in new_links[i]:
                            myTeamsMessage.addLinkButton("Click here for file attached", new_links[i])

                        # Send.
                        myTeamsMessage.send()

                # Convert from list to NumPy array (allows for saving).
                previous_posts = np.array([posts_content, links])

                # Save posts.
                np.save('{}/{}/assignment.npy'.format(year, subject), previous_posts)
            else:
                pass

            # Close web driver.
            driver.quit()

            # Break loop.
            break
        except WebDriverException:
            print("Failed on {} Assignment".format(subject))
        else:
            print("Failed on {} Assignment".format(subject))
            driver.quit()

if __name__ == '__main__':
    script()
