# Fix coach page - add key prop
with open("src/app/coach/page.tsx", "r") as f:
    content = f.read()

old = '<SpotlightCard spotlightColor="rgba(239, 143, 87, 0.1)" className="insight-card mb-4">'
new = '<SpotlightCard key={index} spotlightColor="rgba(239, 143, 87, 0.1)" className="insight-card mb-4">'
content = content.replace(old, new, 1)
print("Added key to coach SpotlightCard")

with open("src/app/coach/page.tsx", "w") as f:
    f.write(content)

# Fix speakers page
with open("src/app/speakers/page.tsx", "r") as f:
    content = f.read()

old = '<SpotlightCard spotlightColor="rgba(197, 244, 75, 0.1)" className="speaker-card">'
new = '<SpotlightCard key={speaker.name} spotlightColor="rgba(197, 244, 75, 0.1)" className="speaker-card">'
content = content.replace(old, new, 1)
print("Added key to speakers SpotlightCard")

with open("src/app/speakers/page.tsx", "w") as f:
    f.write(content)

print("Done!")
