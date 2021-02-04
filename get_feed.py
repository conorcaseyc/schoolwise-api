# Import dependices.
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import numpy as np
import pymsteams
import os
import click

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
            sleep(20)

            # LogIn was successful, proceed to gather posts by Mr. O'Sullivan.
            # Find posts.
            posts = driver.find_element_by_id("journalItems")

            # Get post contents.
            posts = posts.find_elements_by_class_name("journalitem")

            # Iterate through posts.
            posts_content = []
            links = []
            n = 0
            for post in posts:
                # Get author of post.
                author = post.find_element_by_class_name("authorname").text.lstrip().rstrip()
                # Get date of post.
                footer = post.find_element_by_class_name("journalfooter")
                date = footer.find_element_by_css_selector('abbr').get_attribute("title")

                if author == teacher:
                    # Check if post has a file attached.
                    try:
                        item_attached = post.find_element_by_class_name("dnnClear")
                        link = item_attached.find_element_by_css_selector('a').get_attribute('href')
                        text = item_attached.text.lstrip().rstrip()
                        file_output = text + ": " + link + "\n\n"
                    except:
                        link = "no_link"
                        file_output = None

                    # Add links to list.
                    links.append(link)
                    
                    # Get content of post.
                    post_content = post.text
                    header = post.find_element_by_css_selector('p').text
                    footer = post.find_element_by_class_name('journalfooter').text
                    comments = post.find_element_by_class_name('jcmt').text

                    # Remove header and footer.
                    # Header.
                    post_content = post_content.replace(header, '')
                    # Footer.
                    post_content = post_content.replace(footer, '')
                    # Comments section.
                    post_content = post_content.replace(comments, '')

                    # Remove likes section if present.
                    try:
                        likes = post.find_element_by_class_name('likes').text
                        post_content = post_content.replace(likes, '')
                    except:
                        pass

                    # Remove file name if present.
                    try:
                        post_content = post_content.replace(text, '')
                    except:
                        pass

                    # Strip whitespace.
                    content = post_content.lstrip().rstrip()

                    # Combined text of post with file.
                    # Start and end of post output.
                    intro = "SchoolWise API | \n\n"
                    output = intro
                    metadata = "Author: " + teacher + ", Posted on SchoolWise Date: " + date

                    # Attach text content of post.
                    if content != "":
                        output += content + "\n\n"

                    # Attach file information to output.
                    if file_output != None:
                        output += "URL: \n" + file_output
                    
                    # Attach metadata.
                    output += metadata

                    # Attach post to list.
                    posts_content.append(output)

            # Define link to Teams channel.
            teams_channel = teams

            # Have the latest posts at start of list.
            posts_content = posts_content[::-1]
            links = links[::-1]

            # Add check to see if post has already been made.
            try:
                posts = np.load('{}/{}/feed.npy'.format(year, subject))
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

                    # For Teams meeting.
                    keywords = 'Join the conversation on '

                    if not keywords in new_posts[i]:
                        # Compose message.
                        myTeamsMessage.text(new_posts[i])

                        # Add title.
                        myTeamsMessage.title("Feed")
                    else:                        
                        # Get index.
                        index = new_posts[i].find(keywords)
                        indx = new_posts[i].find('URL: ') + 5

                        # Get title of meeting.
                        meeting_name = new_posts[i][indx:index]

                        # Add title.
                        myTeamsMessage.title(
                            "{} | Teams Meeting".format(meeting_name)
                        )

                        # Get time.
                        index += len(keywords)
                        time = new_posts[i][index:index+20]

                        # Create message.
                        # States the message is from the API.
                        content = "SchoolWise API | \n\n"
                        
                        # Content.
                        content += "A MS Teams Meeting is scheduled to take place on {}. Simply click on the link button below to join the call. \n\n".format(
                            time
                        )

                        # Metadata.
                        index = new_posts[i].find("Author: ")
                        content += new_posts[i][index:]

                        # Compose message.
                        myTeamsMessage.text(content)

                    # Add link button.
                    if not "no_link" in new_links[i]:
                        myTeamsMessage.addLinkButton("Click here for link", new_links[i])

                    # Send.
                    myTeamsMessage.send()

            # Convert from list to NumPy array (allows for saving).
            previous_posts = np.array([posts_content, links])

            # Save posts.
            np.save('{}/{}/feed.npy'.format(year, subject), previous_posts)

            # Close web driver.
            driver.quit()
        
            # Break loop.
            break
        except:
            print("Failed on {} Feed".format(subject))
            driver.quit()

if __name__ == '__main__':
    script()
