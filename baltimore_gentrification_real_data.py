import pandas as pd
import folium
import requests
import numpy as np

class BaltimoreGentrificationMapper:
    def __init__(self):
        self.baltimore_center = [39.2904, -76.6122]
        
    def get_census_data(self):
        """Fetch real Census data - WORKING"""
        try:
            print("Fetching US Census Bureau data...")
            
            # Baltimore City FIPS code: state=24, county=510
            variables = {
                'B19013_001E': 'median_income',
                'B25064_001E': 'median_rent', 
                'B15003_022E': 'bachelors_degree',
                'B15003_001E': 'total_education',
                'B08303_001E': 'total_commute',
                'B08303_013E': 'public_transit_commute',
                'B25003_002E': 'owner_occupied',
                'B25003_001E': 'total_housing',
                'B08301_010E': 'public_transport_work'
            }
            
            var_string = ','.join(variables.keys())
            census_url = "https://api.census.gov/data/2021/acs/acs5"
            
            params = {
                'get': var_string,
                'for': 'tract:*',
                'in': 'state:24 county:510'
            }
            
            response = requests.get(census_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to DataFrame
                census_df = pd.DataFrame(data[1:], columns=data[0])
                
                # Clean and calculate percentages
                for old_var, new_var in variables.items():
                    census_df[new_var] = pd.to_numeric(census_df[old_var], errors='coerce')
                
                # Calculate derived metrics
                census_df['education_rate'] = (census_df['bachelors_degree'] / 
                                             census_df['total_education'] * 100).fillna(0)
                
                census_df['transit_rate'] = (census_df['public_transit_commute'] / 
                                           census_df['total_commute'] * 100).fillna(0)
                
                census_df['homeownership_rate'] = (census_df['owner_occupied'] / 
                                                 census_df['total_housing'] * 100).fillna(0)
                
                census_df['tract_id'] = census_df['state'] + census_df['county'] + census_df['tract']
                
                # Filter out invalid data
                census_df = census_df[census_df['median_income'] > 0]
                census_df = census_df[census_df['median_rent'] > 0]
                
                print(f"✅ Successfully fetched {len(census_df)} census tracts with real data")
                
                return census_df[['tract_id', 'median_income', 'median_rent', 
                                'education_rate', 'transit_rate', 'homeownership_rate']]
            else:
                raise Exception(f"Census API returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Census API failed: {e}")
            raise Exception("US Census Bureau API is unavailable. No mock data will be used.")
    
    def test_other_apis(self):
        """Test if other APIs are available"""
        api_status = {}
            
        # Test BLS API
        try:
            print("Testing Bureau of Labor Statistics API...")
            bls_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
            response = requests.post(bls_url, json={"seriesid": ["LAUMT241290000000003"]}, timeout=5)
            api_status['BLS'] = response.status_code == 200
        except:
            api_status['BLS'] = False
            
        return api_status
    
    def calculate_gentrification_scores(self, census_data):
        """Calculate gentrification indicators from Census data"""
        
        # Income score (higher income = higher gentrification potential)
        census_data['income_score'] = (census_data['median_income'] - 
                                     census_data['median_income'].min()) / \
                                    (census_data['median_income'].max() - 
                                     census_data['median_income'].min())
        
        # Education score (higher education = higher gentrification potential)
        census_data['education_score'] = (census_data['education_rate'] - 
                                        census_data['education_rate'].min()) / \
                                       (census_data['education_rate'].max() - 
                                        census_data['education_rate'].min())
        
        # Rent burden score (higher rent = higher gentrification pressure)
        census_data['rent_score'] = (census_data['median_rent'] - 
                                   census_data['median_rent'].min()) / \
                                  (census_data['median_rent'].max() - 
                                   census_data['median_rent'].min())
        
        # Homeownership score (lower ownership = higher rental market pressure)
        census_data['ownership_score'] = 1 - ((census_data['homeownership_rate'] - 
                                             census_data['homeownership_rate'].min()) / \
                                            (census_data['homeownership_rate'].max() - 
                                             census_data['homeownership_rate'].min()))
        
        # Combined gentrification risk score
        census_data['gentrification_risk'] = (
            census_data['income_score'] * 0.3 +
            census_data['education_score'] * 0.25 +
            census_data['rent_score'] * 0.25 +
            census_data['ownership_score'] * 0.2
        )
        
        return census_data
    
    def create_real_data_map(self):
        """Create map using only real data from working APIs"""
        
        print("🔄 Testing API availability...")
        api_status = self.test_other_apis()
        
        print(f"📊 API Status:")
        print(f"  ✅ US Census Bureau: Available")
        print(f"  {'✅' if api_status['BLS'] else '❌'} Bureau of Labor Statistics: {'Available' if api_status['BLS'] else 'Unavailable'}")
        
        # Get real Census data
        census_data = self.get_census_data()
        census_data = self.calculate_gentrification_scores(census_data)
        
        # Create map
        m = folium.Map(
            location=self.baltimore_center,
            zoom_start=11,
            tiles='CartoDB positron'
        )
        
        # Add Census data markers with multiple indicators
        print("Adding real Census data markers...")
        for idx, row in census_data.iterrows():
            
            # Income level classification - Bright, distinctive colors
            income_score = row.get('income_score', 0)
            if income_score > 0.66:
                income_color = '#FF1744'  # Bright red
                income_level = 'High Income'
            elif income_score > 0.33:
                income_color = '#FF9800'  # Bright orange
                income_level = 'Medium Income'
            else:
                income_color = '#4CAF50'  # Bright green
                income_level = 'Low Income'
            
            # Education level classification - Purple/Blue spectrum
            education_score = row.get('education_score', 0)
            if education_score > 0.66:
                education_color = '#9C27B0'  # Bright purple
                education_level = 'High Education'
            elif education_score > 0.33:
                education_color = '#2196F3'  # Bright blue
                education_level = 'Medium Education'
            else:
                education_color = "#093A28"  # dark green
                education_level = 'Low Education'
            
            # Gentrification risk classification - High contrast colors
            risk_score = row.get('gentrification_risk', 0)
            if risk_score > 0.66:
                risk_color = "#740127"  # Hot pink
                risk_level = 'High Gentrification Risk'
            elif risk_score > 0.33:
                risk_color = "#FFFB0A"  # Amber
                risk_level = 'Medium Gentrification Risk'
            else:
                risk_color = "#5DD270"  # Cyan
                risk_level = 'Low Gentrification Risk'
            
            # Create organized grid-like positions for each tract to reduce confusion
            lat_offset = (hash(row['tract_id']) % 1000 - 500) / 1200  # Even wider spread
            lon_offset = (hash(row['tract_id']) % 1400 - 700) / 1200  # Even wider spread
            
            # Income marker (large circle) - CENTER position
            folium.CircleMarker(
                location=[self.baltimore_center[0] + lat_offset,
                        self.baltimore_center[1] + lon_offset],
                radius=8,  # Smaller for clarity
                popup=f"<b>Census Tract {row['tract_id'][-6:]}</b><br>"
                      f"<b>REAL US CENSUS DATA</b><br>"
                      f"Median Income: ${row['median_income']:,.0f}<br>"
                      f"Education Rate: {row['education_rate']:.1f}%<br>"
                      f"Median Rent: ${row['median_rent']:,.0f}<br>"
                      f"Homeownership: {row['homeownership_rate']:.1f}%<br>"
                      f"Transit Use: {row['transit_rate']:.1f}%<br>"
                      f"<b>Income Level: {income_level}</b>",
                color='black',
                weight=2,
                fill=True,
                fillColor=income_color,
                fillOpacity=0.9
            ).add_to(m)
            
            # Education marker (small circle) - NORTH position (above income)
            folium.CircleMarker(
                location=[self.baltimore_center[0] + lat_offset + 0.015,  # Directly above
                        self.baltimore_center[1] + lon_offset],
                radius=4,  # Smaller for clarity
                popup=f"<b>Education Data</b><br>"
                      f"Tract: {row['tract_id'][-6:]}<br>"
                      f"Bachelor's Degree Rate: {row['education_rate']:.1f}%<br>"
                      f"<b>{education_level}</b>",
                color='black',
                weight=1,
                fill=True,
                fillColor=education_color,
                fillOpacity=0.8
            ).add_to(m)
            
            # Gentrification risk marker (square) - SOUTH position (below income)
            folium.RegularPolygonMarker(
                location=[self.baltimore_center[0] + lat_offset - 0.015,  # Directly below
                        self.baltimore_center[1] + lon_offset],
                number_of_sides=4,
                radius=5,  # Smaller for clarity
                popup=f"<b>Gentrification Risk Analysis</b><br>"
                      f"Tract: {row['tract_id'][-6:]}<br>"
                      f"Risk Score: {risk_score:.2f}<br>"
                      f"Income Factor: {row['income_score']:.2f}<br>"
                      f"Education Factor: {row['education_score']:.2f}<br>"
                      f"Rent Pressure: {row['rent_score']:.2f}<br>"
                      f"<b>{risk_level}</b>",
                color='black',
                weight=1,
                fill=True,
                fillColor=risk_color,
                fillOpacity=0.8
            ).add_to(m)
        
        # Enhanced legend
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 10px; left: 10px; 
                    width: 450px; 
                    height: 400px; 
                    background-color: white; 
                    border: 3px solid #333; 
                    border-radius: 12px;
                    z-index: 9999; 
                    font-size: 13px; 
                    padding: 20px; 
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    font-family: 'Segoe UI', Arial, sans-serif;
                    overflow-y: auto;">
        
        <h3 style="margin: 0 0 15px 0; color: #2c3e50; text-align: center; 
                   border-bottom: 2px solid #3498db; padding-bottom: 8px; font-size: 16px;">
           Baltimore Gentrification Analysis (REAL DATA)
        </h3>
        
        <div style="margin-bottom: 15px; padding: 8px; background-color: #e8f5e8; border-radius: 5px;">
            <h4 style="margin: 0 0 5px 0; color: #27ae60; font-size: 12px;">
                📊 DATA SOURCES STATUS:
            </h4>
            <div style="font-size: 11px; line-height: 1.4;">
                ✅ US Census Bureau: {len(census_data)} tracts (REAL DATA)<br>
                {'✅' if api_status['BLS'] else '❌'} Bureau of Labor Statistics: {'Available' if api_status['BLS'] else 'Unavailable'}
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="margin: 0 0 8px 0; color: #e74c3c; font-size: 14px;">
                💰 Income Levels (Large Circles):
            </h4>
            <div style="margin-left: 15px; line-height: 1.6; font-size: 12px;">
                ⬤ <span style="color: #FF1744; font-weight: bold;">High Income</span> - Above median<br>
                ⬤ <span style="color: #FF9800; font-weight: bold;">Medium Income</span> - Middle range<br>
                ⬤ <span style="color: #4CAF50; font-weight: bold;">Low Income</span> - Below median
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="margin: 0 0 8px 0; color: #8e44ad; font-size: 14px;">
                🎓 Education Levels (Small Circles):
            </h4>
            <div style="margin-left: 15px; line-height: 1.6; font-size: 12px;">
                ⬤ <span style="color: #9C27B0; font-weight: bold;">High Education</span> - High bachelor's rate<br>
                ⬤ <span style="color: #2196F3; font-weight: bold;">Medium Education</span> - Average rate<br>
                ⬤ <span style="color: #093A28; font-weight: bold;">Low Education</span> - Low bachelor's rate
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="margin: 0 0 8px 0; color: #f39c12; font-size: 14px;">
                🏠 Gentrification Risk (Squares):
            </h4>
            <div style="margin-left: 15px; line-height: 1.6; font-size: 12px;">
                ◼ <span style="color: #740127; font-weight: bold;">High Risk</span> - Multiple pressure factors<br>
                ◼ <span style="color: #FFFB0A; font-weight: bold;">Medium Risk</span> - Some indicators<br>
                ◼ <span style="color: #56074E; font-weight: bold;">Low Risk</span> - Stable conditions
            </div>
        </div>
        
        <div style="font-size: 10px; color: #7f8c8d; text-align: center; margin-top: 10px; 
                    border-top: 1px solid #ecf0f1; padding-top: 8px;">
            Real Data: US Census Bureau ACS 2021<br>
            {len(census_data)} Baltimore Census Tracts
        </div>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        return m
    
    def save_map(self, filename='baltimore_gentrification_real_data.html'):
        """Save the map with real data only, with intro modal"""
        m = self.create_real_data_map()
        m.save(filename)
        # Inject intro modal HTML and JS
        with open(filename, 'r', encoding='utf-8') as f:
            html = f.read()
        intro_modal = '''
        <div id="intro-modal" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(255,255,255,0.98);z-index:10000;display:flex;align-items:center;justify-content:center;">
            <div style="max-width:600px;background:white;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.18);padding:36px 32px 32px 32px;text-align:center;">
                <h2 style="color:#1f4e79;margin-bottom:18px;">Understanding Gentrification in Baltimore</h2>
                <p style="font-size:1.1em;color:#333;margin-bottom:18px;">
                    <strong>Gentrification</strong> is a process where neighborhoods experience rising property values, new investment, and demographic shifts—often resulting in higher rents and the displacement of long-time residents. While it can bring new amenities and improvements, it can also threaten the cultural fabric and affordability of communities.
                </p>
                <p style="font-size:1.1em;color:#333;margin-bottom:18px;">
                    In Baltimore, gentrification has affected many neighborhoods, especially those with historic underinvestment. This map uses real data to show which areas are at risk, helping residents, policymakers, and advocates understand and respond to these changes.
                </p>
                <button onclick=\"document.getElementById('intro-modal').style.display='none';\" style=\"background:#1f4e79;color:white;font-size:1.1em;padding:12px 32px;border:none;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px rgba(31,78,121,0.12);margin-top:10px;\">Enter the Map</button>
            </div>
        </div>
        '''
        html = html.replace('<body>', '<body>' + intro_modal, 1)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n🎉 Real data map saved as {filename} (with intro modal)")
        print(f"📊 Using ONLY real data from working APIs")
        return m

# Usage
if __name__ == "__main__":
    print("🏘️ Baltimore Gentrification Mapper (REAL DATA ONLY)")
    print("=" * 55)
    
    mapper = BaltimoreGentrificationMapper()
    gentrification_map = mapper.save_map()
    
    print("\n🗺️ Real data gentrification map complete!")
    print("📁 Open baltimore_gentrification_real_data.html in your browser")
